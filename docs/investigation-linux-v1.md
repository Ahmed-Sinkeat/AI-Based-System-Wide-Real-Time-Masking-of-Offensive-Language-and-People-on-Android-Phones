# HaramBlurr — Technical Investigation, Linux v1

> **Paused — plan B (2026-10-06).** The project moved to **Android first**. See [`investigation-android-v1.md`](investigation-android-v1.md) and [`p0-results-android-v1.md`](p0-results-android-v1.md). The model findings here (§5–§9) still apply to Android. The Hyprland plugin work is on hold.

**Real-Time System-Level Visual Filtering System**
Scope: Linux (Wayland) only. Android is out of scope for v1.
Date: 2026-10-02 · Status: investigation. P0 benchmarks done: see [`p0-results-linux-v1.md`](p0-results-linux-v1.md)

---

## 0. Verdict (short)

| Question | Answer |
|---|---|
| Is it possible? | **Yes.** On Wayland the compositor already holds every app's pixels as GPU textures before they reach the screen. A filter placed there needs no screen capture. |
| Where should it run? | **Inside the compositor**, as a thin plugin. v1 targets **Hyprland**, the compositor on the dev machine. Inference runs in a **separate daemon process**. |
| Which architecture? | Plugin: per-window downscale, async readback, mask shader. Daemon: segmentation model and temporal logic. Unanalyzed pixels are blurred until a result arrives (**fail-closed**). |
| Which model? | A real-time **instance segmentation** model, fine-tuned on screen-domain data that a large teacher (SAM 3) labels. **Measured on this laptop:** YOLO11s/26s-seg INT8 (28–31 ms). RF-DETR is more accurate but 73–147 ms, too slow on Iris Xe. |
| What accuracy? | **Measured on COCO and a synthetic 1080p feed window.** 86–95% of large people are fully hidden. In a feed-like window a single pass hides only 16–26% of small people, 35–69% with 2×2 tiling. Real screen content is still unmeasured (§9). |
| What performance cost? | **Measured:** daemon 20–31 ms/frame (YOLO n/s INT8, Iris Xe) at 1 CPU core, ~280 MB RAM. Compositor readback 2.6 ms, mask pass 3.6 ms. Fail-closed blur ≈ 2–3 frames per change. Power not measured. |
| Platform restrictions? | Works for every Wayland and XWayland app on the chosen compositor. It is tied to one compositor, and the Hyprland plugin API is unstable (rebuild on each version). Direct scanout must be disabled. |

The main risk is the **accuracy-to-latency ratio on weak hardware**, not the OS integration. P0 confirmed this: speed is fine, and small-person recall is the open problem.

---

## 1. Dev / target machine (measured)

```
CPU    Intel Core i5-1135G7 (4C/8T, Tiger Lake)
GPU    Intel Iris Xe (TigerLake-LP GT2, 80 EU), integrated, shared memory
RAM    7.5 GiB
NPU    none
OS     Arch Linux, Hyprland 0.56.2 (Wayland), Python 3.14, OpenCV 5.0
```

Implications:
- The inference backend is **OpenVINO on the Iris Xe GPU**. CUDA/TensorRT do not apply here.
- Memory is unified (iGPU), so moving frames from GPU to CPU is cheap. Zero-copy is possible later.
- Published numbers are measured on NVIDIA T4/TensorRT. They overstate speed on this machine: **measured** 8× for YOLO11n-seg (15 ms) and 24× for RF-DETR-Seg-N (81 ms).
- No root is needed for GPU compute. The Intel compute runtime runs from user space (`bench/env.sh`).

---

## 2. Where the filter can sit in the Linux display path

```
App renders ─► wl_buffer (shm or dmabuf) ─► Compositor ─► composite ─► KMS/DRM ─► Display
   (D)                                        (B)                       (C)
                                                       └─► screencopy/portal (A)
```

| Option | How | No flash? | All apps? | No screencast? | Verdict |
|---|---|---|---|---|---|
| **A. Capture + overlay** | Portal/PipeWire or `ext-image-copy-capture`, then infer, then draw on a layer-shell overlay | ❌ content is shown before analysis | ✅ | ❌ (this is screencasting) | Today's approach. It causes the problems listed in the brief. |
| **B. Compositor plugin** | Hook window rendering. Read each window's texture, analyze it, draw the mask before the frame is composited. | ✅ the compositor decides what reaches the screen | ✅ every Wayland and XWayland window | ✅ | **Chosen.** |
| C. DRM/KMS level | Writeback connectors, kernel hooks | ⚠️ | ✅ | ✅ | Only the final composited frame. Driver-specific, no per-window info, very hard. Rejected. |
| D. Per-app layer | Vulkan/GL layer (vkBasalt-style) or `LD_PRELOAD` | ✅ | ❌ GPU apps only, opt-in per app | ✅ | Misses shm apps. Not system-level. Rejected. |
| E. Own compositor | wlroots/Smithay compositor written from scratch | ✅ | ✅ | ✅ | Too much work for v1. Users would have to switch desktops. |

### Compositor choice for v1

| Compositor | Extension point | Pros | Cons |
|---|---|---|---|
| **Hyprland** | C++ plugin (`hyprpm`), render-pass API, GLES 3 | Installed on the dev machine. Per-window shader plugins already exist: Hypr-DarkWindow, HyprWindowShade [3][4]. | No stable API, so the plugin must be rebuilt per version. A Vulkan renderer is in progress and may change texture access [6]. |
| Wayfire | C++ plugin, built for this | Plugin-first design. Has a per-view filter plugin. | Small user base. Not on the dev machine. |
| KWin (Plasma) | Effects (`OffscreenEffect`) | Largest user base. More stable API. | Heavier stack and build. |
| GNOME/Mutter | JS extensions | Large user base | Little access to window textures. Poor fit. |

**Decision:** Hyprland for v1, **pinned to one version** (0.56.x, GLES renderer). Keep the plugin thin and put all logic in the daemon, so a port to KWin or Wayfire means rewriting only the plugin.

**Precedent:** Hypr-DarkWindow already applies a custom fragment shader to selected windows through window rules [3]. That covers half of the compositor work (mask application). The new parts are readback and the mask texture.

---

## 3. Proposed architecture

```
┌──────────────────────── Hyprland process ────────────────────────┐
│  per window (toplevel + subsurfaces), on commit/damage:          │
│   1. render window tree → small FBO (long side 640), RGBA        │
│      (the compositor's own shader handles XRGB/ARGB2101010/NV12) │
│   2. async readback (PBO) → shared-memory ring (memfd)           │
│   3. draw window with mask shader:                               │
│        pending damage  → blurred / pixelated  (fail-closed)      │
│        analyzed        → blur where mask = 1                     │
│   never waits on the daemon — the render thread must not block   │
└───────────────┬─────────────────────────────▲────────────────────┘
                │ unix socket in $XDG_RUNTIME_DIR (0600)
                │ {window_id, commit_seq, w, h, shm_offset}
                ▼                             │ {window_id, commit_seq, mask 160×160 | boxes}
┌──────────────────────── haramblurr daemon ───────────────────────┐
│  OpenVINO (Iris Xe GPU) · seg model (ONNX/IR)                    │
│  temporal logic: hysteresis, tracking, scene-cut detection       │
│  mask post-process: threshold → dilate → downsample              │
└──────────────────────────────────────────────────────────────────┘
```

Key choices:
- **Per window, not per screen.** Unchanged windows (a terminal, a static editor) cost nothing. Each window is analyzed at its own scale, which helps small objects. Layer surfaces (wallpaper, panels) are analyzed the same way. A wallpaper can contain people.
- **Damage-driven.** Work happens only on commits that damage the window. Idle desktop means about 0% inference load.
- **Separate process.** A crash or stall in the model must not freeze the desktop. If the daemon is down, the plugin blurs all newly changed content and shows an indicator.
- **Readback cost is trivial.** 640×360 RGBA ≈ 0.9 MB/frame, about 55 MB/s at 60 FPS on unified memory. Zero-copy (dmabuf → OpenVINO remote tensor) is a later optimization. `ponytail:` PBO readback first, dmabuf import if the copy shows up in profiles.
- **Use opaque obfuscation, not light blur.** A light Gaussian blur still shows silhouettes. Use strong pixelation or a solid fill (one shader pass, cheaper too). Make the strength configurable.
- **Compositor settings:** set `render:direct_scanout = 0`. Fullscreen direct scanout skips composition and would bypass the filter. Check that the screencopy/screenshare path also renders through the filter, or it will leak unfiltered pixels.
- **Model format:** ONNX as the interchange format, OpenVINO IR at runtime. The same ONNX model can later target Android, which costs nothing now.

---

## 4. Preventing content from showing before analysis (Q5)

New pixels have to be handled somehow before the model has seen them. Three policies:

| Policy | Shows unanalyzed pixels? | Cost |
|---|---|---|
| Show, then blur later (screencast tools) | **Yes**. This is the flash problem. | none |
| **Fail-closed blur of pending damage** | No | Changed regions are blurred for about 1 inference latency. Scrolling looks briefly blurred. |
| Hold frame (delay presentation by L ms) | No | Adds L ms latency to everything. The plugin must copy buffers, because clients reuse them. Video drifts out of sync with audio. |

**v1 uses fail-closed.** It is the simplest policy that never leaks, and it needs no frame queue.

Refinements, all cheap:
- Only damaged regions turn blurred. The rest of the window keeps its last result.
- Carry existing masks forward between frames, so known targets stay blurred.
- **Scene-cut detection** (histogram difference, about 0.1 ms): on a cut, blur the whole window until the first result.
- **v1.1:** a bounded hold queue for video windows. Hold up to about 40 ms, then fall back to blur. Video can be delayed by roughly 40 ms before audio visibly leads (EBU R37 allows audio up to +40 ms early). Any longer hold drifts out of lip-sync.

Latency budget at 60 Hz (16.7 ms/frame):

| Stage | Target |
|---|---|
| Downscale and readback | ≤ 2 ms |
| Inference (Iris Xe, n/s INT8, 640, incl. pre/post) | **20–31 ms measured** (p95 30–40 ms) |
| Post-process, mask upload, shader | ≤ 2 ms |
| **Fail-closed blur window** | about 1–4 frames per change |

If inference stays under 1 frame, the fail-closed blur becomes almost invisible. On Iris Xe it probably won't, so expect 2–4 frames of blur after each change.

---

## 5. Boxes vs masks (Q6, Q7)

| | Bounding boxes | Instance masks |
|---|---|---|
| Hides only the target | ❌ also hides background | ✅ |
| Robust on small/far people | ✅ | ⚠️ masks are noisy below about 32 px |
| Cost | lower | slightly higher (seg head) |
| Fails safe | ✅ over-covers | ⚠️ thin gaps at edges |

**Decision:** an instance segmentation model, which outputs both. Render the mask **dilated by a margin** (about 4–8% of the instance height) with feathered edges. For instances under about 32 px, render the **box** instead of the mask.

---

## 6. Model candidates (Q8)

Runtime candidates (student). COCO numbers come from vendor docs on T4/TensorRT and are relative only:

| Model | COCO mask AP (approx.) | T4 latency | License | Note |
|---|---|---|---|---|
| RF-DETR-Seg N | 40.3 [1] | 3.4 ms | Apache-2.0 [2] | Best accuracy per ms among real-time seg models. DINOv2 backbone. Transformer ops on OpenVINO iGPU need checking. |
| RF-DETR-Seg S/M | higher | ~5–8 ms | Apache-2.0 | Probably too slow for Iris Xe at frame rate |
| YOLO11n-seg | ~32 | ~1.8 ms | **AGPL-3.0** | Most mature OpenVINO export. Easiest first baseline. |
| YOLO11s-seg | ~38 | ~2.9 ms | AGPL-3.0 | |

Licenses: AGPL is fine for an open-source graduation project. It matters only if the project goes closed-source. Check the license of each checkpoint before use.

Teacher candidates (training/labeling only, never at runtime):

| Model | Role |
|---|---|
| **SAM 3** (Meta, Nov 2025) [7] | Takes a text prompt (e.g. "person") and returns masks for every instance, in images and video, with tracking. It can auto-label people seen from behind, from far away, or partly hidden. This is the main teacher. |
| SAM 2.1 / EdgeTAM | Propagates masks across video, for temporal labels |
| Sapiens (Meta) | Body-part segmentation, if v2 needs part-level targets |

Most real-time seg models are trained on COCO, which is mostly photos. Screen content looks different: thumbnails, compression artifacts, text overlays, UI chrome, anime and illustrations, game renders. **Fine-tuning on screen-domain data will likely matter more than which model is picked.**

---

## 7. Teacher–student / distillation (Q9, Q10)

**Yes, it is useful**, in its simplest form: **offline pseudo-labeling**.

```
Unlabeled screen-domain frames (screen recordings of real usage:
  feeds, video sites, news, games, anime) + CrowdHuman / OCHuman / COCO-person
        │
        ▼
SAM 3 ("person") → masks + boxes  ── human review of val/test only
        │
        ▼
Fine-tune RF-DETR-Seg-N or YOLO11n/s-seg on pseudo-labels
        │
        ▼
Export ONNX → OpenVINO IR (FP16, then INT8 with calibration)
```

- CrowdHuman has full-body boxes even under occlusion, and many people seen from behind. It targets the "back and far away" failure from the brief directly.
- Feature-level distillation (matching teacher features or logits) adds work. Try it only if the pseudo-label student falls short of the target. `ponytail:` pseudo-labels first, feature distillation if the recall gap stays above about 5 points.
- INT8 quantization on Iris Xe is likely needed for speed. Measure the accuracy drop separately.

---

## 8. Temporal processing (Q13, Q14, Q17)

- **How often to run the model:** on every damaged commit, as fast as it can go. The daemon drops stale frames and only processes the latest commit per window. A static window runs zero times per second. Video runs at about the model's max FPS.
- **Hysteresis (asymmetric):** blur as soon as one detection is above threshold. Unblur only after *K* consecutive misses (K ≈ 5). This removes flicker false negatives cheaply.
- **Tracking:** ByteTrack on boxes (cheap, CPU) keeps IDs stable and fills in boxes for short detection dropouts. Mask-propagation trackers (SAM 2/EdgeTAM) are too heavy for Iris Xe at runtime. Use them as teachers only.
- **Fast motion and video:** fail-closed covers new content. Dilated masks cover motion between inferences. Scene-cut detection forces a full-window blur.
- **Scrolling:** the whole window is damaged, so it falls back to fail-closed blur. `ponytail:` blur while scrolling. Shifting masks by an estimated scroll offset (phase correlation) is possible if it feels bad.

---

## 9. Accuracy: hard cases, false positives, what's achievable (Q16, Q18, Q19, Q20)

**Hard cases:** people under about 20 px at model input, people seen from behind, partial crops (only arms or legs), heavy occlusion, crowds, unusual poses, low light, motion blur, anime, illustrations, 3D game characters, reflections. Common false-positive triggers: statues, mannequins, dolls, posters, figure-shaped objects.

**Small/far people:** downscaling a 1920×1080 window to 640 shrinks everything 3×. Mitigations, in order of cost:
1. Per-window inference (already in the design)
2. A tiled pass (2×2) at a lower rate as a recall booster. It costs about 4× per run, so run it every N frames. `ponytail:` single pass, add tiling if small-person recall misses the target.

**Reducing false positives** without hurting recall:
- Tune per-class thresholds on a **screen-domain validation set**, not on COCO.
- Mine hard negatives (statues, mannequins) into training.
- In this product a false positive costs little (a needless blur) and a false negative costs a lot. **Pick the operating point by recall first**, e.g. recall ≥ 0.95, then the lowest false-positive rate at that recall.

**Target definition is the biggest accuracy decision.** It is not settled yet:

| Target | Achievable accuracy | Fails safe? |
|---|---|---|
| All persons | Highest. Person is the best-trained class everywhere. | ✅ |
| Persons filtered by an attribute (e.g. gender) | Much lower: a second classifier is unreliable from behind, far away, or partly visible | ❌ an attribute error means exposure |
| Exposure/nudity regions | A separate model and dataset | depends |

Recommendation: v1 target = **all persons**. It is the only target where the fail-closed design degrades safely. An attribute filter can be a v2 stage stacked on top.

**What's achievable:** no published benchmark covers screen content, so the number has to be measured. On COCO, small-object AP for real-time models is typically about a third to half of large-object AP. Expect strong results on large people and weak results on small ones.

**Metrics** that fit the product better than mAP:

| Metric | Definition |
|---|---|
| Pixel recall | % of target pixels covered by blur (per frame, by size bucket) |
| Exposure frames | Frames in which any target pixel is visible unblurred. **Primary safety metric.** |
| Over-blur ratio | % of blurred pixels that are not the target |
| Blur-pending time | ms that changed content stays blurred while awaiting analysis |
| Inference ms, CPU %, GPU %, RAM, power | Measured on the dev machine |

Test set: about 1–2k frames of human-verified screen recordings across categories (feeds, video, games, anime, news, UI-only negatives).

---

## 10. Answers to the research questions (Linux scope)

| # | Question | Answer |
|---|---|---|
| 1 | Where in the Linux display path? | Compositor plugin, per window, before composition (§2) |
| 2 | Android | Out of scope for v1 |
| 3 | Avoid screencasting entirely? | Yes. The compositor already has the textures (§2-B) |
| 4 | All apps? | All Wayland and XWayland windows and layer surfaces on Hyprland. Not other compositors, X11 sessions, or the TTY. Direct scanout must be off. |
| 5 | No flash before analysis? | Fail-closed blur of pending damage (§4) |
| 6–7 | Region method / boxes vs masks | Instance seg, dilated mask, box for small instances (§5) |
| 8 | Best real-time models | RF-DETR-Seg N, YOLO11n/s-seg baseline (§6) |
| 9 | Train a specialized model? | Yes, by fine-tuning on screen-domain pseudo-labels (§7) |
| 10 | Knowledge distillation useful? | Yes, as SAM 3 teacher pseudo-labels (§7) |
| 11 | Acceptable latency | ≤ 1 frame of added UI latency. ≤ about 40 ms of hold for video (A/V sync). Fail-closed blur ≤ about 4 frames per change. |
| 12 | CPU/GPU/RAM | Not measured yet. Step P0 (§11) |
| 13 | Inferences per second | Event-driven, latest-commit-wins. 0 when idle, model max FPS during video (§8) |
| 14 | Tracking between inferences | ByteTrack and hysteresis at runtime. SAM-family trackers offline only (§8) |
| 15 | Same engine on Android | Yes, via an ONNX model and a portable daemon. Plugin/HAL integration differs. |
| 16 | Hard cases | §9 |
| 17 | Video / fast motion | Fail-closed, dilation, scene-cut detection. Optional hold queue in v1.1 (§4, §8) |
| 18 | Far / partial / from behind | Per-window scale, tiling, CrowdHuman, SAM 3 pseudo-labels (§7, §9) |
| 19 | Reduce false positives | Screen-domain thresholds, hard negatives, recall-first operating point (§9) |
| 20 | Achievable accuracy | Must be measured on a screen-domain test set. Weak spot: small people (§9) |

---

## 11. Next steps (the order matters, cheapest answers first)

| Step | What | Answers | Size |
|---|---|---|---|
| **P0 — Offline bench** ✅ done ([results](p0-results-linux-v1.md)) | Python venv with OpenVINO, rfdetr and ultralytics. Record about 10 min of real usage (`wf-recorder`). Run YOLO11n/s-seg and RF-DETR-Seg-N on CPU and Iris Xe GPU, FP16/INT8. Measure ms/frame and pixel recall by size bucket. | Q8, Q12, Q20. Is Iris Xe fast enough at all? | days |
| P1 — Plugin skeleton | Fork Hypr-DarkWindow. Add a per-window FBO downscale, PBO readback to shm, and a mask texture uniform with a pixelate shader. Use a fake daemon that returns fixed boxes. | Q1, Q4, Q5 on real hardware. Compositor frame-time cost. | ~1–2 weeks |
| P2 — Daemon | OpenVINO inference, hysteresis, ByteTrack, scene cut. Wire it to the plugin. | End-to-end latency, blur-pending time | ~1–2 weeks |
| P3 — Data & distillation | Screen-domain dataset, SAM 3 pseudo-labels, fine-tune, test set | Q9, Q10, Q16–Q20 | weeks |

**Go/no-go after P0:** if no candidate reaches about 15 FPS at 640 on Iris Xe with acceptable recall, change the target hardware (dGPU/NPU laptop) or lower the input size before writing any compositor code.
**Result:** GO on speed (YOLO-s INT8 at 31–34 FPS). Recall on small people is not yet acceptable. Tiling and P3 screen-domain fine-tuning are the levers.

---

## 12. Out of scope for v1 / risks

- **Out of scope:** Android, X11 sessions, compositors other than Hyprland, tamper resistance (the user can disable the plugin; this is a self-chosen filter, not an enforcement tool), HDR, multi-GPU.
- **Risks:**
  - The Hyprland API can break between versions, so pin the version.
  - The Vulkan renderer may change texture access [6].
  - A plugin bug crashes the whole session, so keep the plugin minimal.
  - Weak hardware forces a small model, which lowers the accuracy ceiling.
- **Privacy:** the daemon sees everything on screen, including passwords. Frames stay in memory only. No logging of frames, no network access, and the socket is 0600 in `$XDG_RUNTIME_DIR`.

---

## Sources

1. [RF-DETR Segmentation checkpoints (Roboflow blog)](https://blog.roboflow.com/rf-detr-segmentation/)
2. [RF-DETR paper, ICLR 2026 (arXiv 2511.09554)](https://arxiv.org/pdf/2511.09554)
3. [Hypr-DarkWindow: per-window shaders in Hyprland](https://github.com/micha4w/Hypr-DarkWindow)
4. [HyprWindowShade: per-window shader plugin](https://github.com/the-bmt/HyprWindowShade)
5. [YOLO11 + OpenVINO on LattePanda MU (iGPU seg ~15 FPS)](https://www.lattepanda.com/blog-323240.html)
6. [Hyprland Vulkan renderer WIP (PR #13272)](https://github.com/hyprwm/Hyprland/pull/13272)
7. [SAM 3: Segment Anything with Concepts (arXiv 2511.16719)](https://arxiv.org/pdf/2511.16719)
8. [Hyprland rendering pipeline (DeepWiki)](https://deepwiki.com/hyprwm/Hyprland/6.1-rendering-pipeline)
