# HaramBlurr — P0 Measurement Results (Linux v1)

> **Paused — plan B (2026-10-06).** The project moved to **Android first**. See [`investigation-android-v1.md`](investigation-android-v1.md) and [`p0-results-android-v1.md`](p0-results-android-v1.md). The model accuracy results here (§4–§5) still apply. The speed results are for the laptop only.

Date: 2026-10-02 (overnight run) · Machine: i5-1135G7, Iris Xe iGPU, 7.5 GiB RAM, Hyprland 0.56.2
Scope: step P0 of [`investigation-linux-v1.md`](investigation-linux-v1.md) §11. Offline benchmarks only, no compositor code yet.
Everything here is a proposal input. Every choice can still change.

Raw data: `bench/results/*.json`, `bench/results/latency.csv`, `bench/results/SUMMARY.md` (all tables).
Reproduce: `cd bench && source env.sh && ./run_all.sh` (details in [Reproducing](#reproducing)).

---

## 1. Bottom line

| Question | Measured answer |
|---|---|
| Can this laptop run the model in real time? | **Yes, for YOLO-class n/s models.** The daemon loop takes 20–31 ms per frame (p50) with INT8 on the Iris Xe GPU. **RF-DETR does not fit:** 73–147 ms per frame (7–13 FPS). |
| Is the compositor-side cost small? | **Yes.** Downscaling a 1080p window and reading it back asynchronously takes 2.6 ms (p50). Mask upload plus the pixelate pass at 1080p takes 3.6 ms (p50). |
| What latency does fail-closed blur add? | About **40–50 ms per content change** (2–3 frames at 60 Hz) with a YOLO-s INT8 model. This is the time changed content stays blurred before it is shown unblurred. |
| Is accuracy good enough? | **Not yet.** Large people are fine: 86–95% fully hidden. **Small people in feed-like windows are the failure:** a single 640-px pass over a 1080p window fully hides only 16–26% of them. 2×2 tiling lifts that to 35–69%. Accuracy is now the bottleneck, not speed. |
| Which model for v1 on this hardware? | **YOLO11s-seg or YOLO26s-seg, INT8, with 2×2 tiling on large windows.** RF-DETR is clearly more accurate but 3–5× too slow on this iGPU. It fits better as a stronger-hardware option or as a slow second opinion. |
| Does INT8 hurt? | **YOLO: no** (≤1.5 points). **RF-DETR: yes**, and it is *slower* on this GPU. The GPU plugin also produces empty masks for it (§6). |

---

## 2. Setup

| Item | Value |
|---|---|
| Runtime | OpenVINO 2026.4.1, GPU plugin on Intel compute runtime 26.31 + IGC 2.40 |
| GPU driver install | **No root.** The Arch packages were extracted into `bench/neo/` and activated with `OCL_ICD_VENDORS` (`bench/env.sh`). |
| Models | YOLO11n/s-seg, YOLO26n/s-seg (Ultralytics 8.4, 640×640). RF-DETR-Seg Nano/Small/Medium (rfdetr, 312/384/432 px). Each in FP16 and INT8. |
| INT8 | YOLO: Ultralytics export with NNCF, coco128 calibration. RF-DETR: NNCF PTQ, coco128, SmoothQuant **off** (§6). |
| Accuracy data | COCO val2017: all 2693 images with people (10 777 person instances) and 500 person-free images |
| "Screen" data | Synthetic 1920×1080 feed window: header bar, 3×2 grid of COCO photos as 600×440 tiles, caption text. 100 windows, 2 320 person instances (914 small, 807 medium, 599 large). |
| Inference path | Torch-free numpy/OpenCV pre- and post-processing (`bench/ov_seg.py`). Checked against Ultralytics: person mask AP 0.402 vs 0.399 on the same 100 images. |

**Metric used throughout.** A person counts as *hidden* if at least 90% of their pixels fall under the blur region. Results are bucketed by COCO area: small < 32², medium < 96², large ≥ 96² px. Other metrics:
- *Pixel recall:* the share of all person pixels covered.
- *Over-blur:* the share of blurred pixels that are not a person.
- *False alarm:* the share of person-free images where anything was blurred.

The blur region is the mask dilated by about 1% of the image's long side, unless stated otherwise.

---

## 3. Speed

### 3.1 Raw inference (OpenVINO `benchmark_app`, batch 1, latency mode, quiet machine)

| model | input | GPU ms (median) | GPU FPS | CPU ms | CPU FPS |
|---|---|---|---|---|---|
| yolo11n-seg FP16 | 640 | 15.0 | 59 | 42.9 | 22 |
| yolo11n-seg INT8 | 640 | **11.6** | 73 | **18.2** | 50 |
| yolo26n-seg FP16 | 640 | 17.9 | 55 | 40.6 | 24 |
| yolo26n-seg INT8 | 640 | 14.0 | 62 | 18.2 | 48 |
| yolo11s-seg FP16 | 640 | 30.7 | 31 | 127.9 | 8 |
| yolo11s-seg INT8 | 640 | 25.8 | 38 | 44.9 | 22 |
| yolo26s-seg FP16 | 640 | 39.5 | 24 | 133.6 | 7 |
| yolo26s-seg INT8 | 640 | 28.5 | 35 | 47.1 | 20 |
| rfdetr-seg-nano FP16 | 312 | 80.7 | 12 | 217.0 | 4.5 |
| rfdetr-seg-nano INT8 | 312 | 118.0 ⚠ | 8 | 107.2 | 8.8 |
| rfdetr-seg-small FP16 | 384 | 138.4 | 7 | 300.7 | 3.2 |
| rfdetr-seg-small INT8 | 384 | 173.9 ⚠ | 6 | 145.3 | 6.8 |
| rfdetr-seg-medium FP16 | 432 | 144.9 | 7 | 388.4 | 2.5 |

- Vendor T4 numbers do not transfer. RF-DETR-Seg-Nano is rated 3.4 ms on T4 and takes **81 ms** here, about 24× slower. YOLO11n is rated about 1.8 ms and takes 15 ms here, about 8× slower. The transformer (DINOv2) backbone runs poorly on this iGPU.
- ⚠ INT8 makes RF-DETR **slower** on the GPU. It only helps on the CPU (2× faster).
- Cold GPU compile takes 0.4–9.5 s per model. Use a precompiled cache (§7).

### 3.2 Daemon loop (`runtime.py`: 640×360 frame in, masks out, conf 0.25, 30 s flat-out, quiet machine)

| model | device | p50 ms | p95 ms | p99 ms | FPS | CPU (100 = 1 core) | RSS MB |
|---|---|---|---|---|---|---|---|
| yolo11n-seg INT8 | GPU | **20.4** | 30.4 | 34.6 | 46.7 | 99 | 282 |
| yolo26n-seg INT8 | GPU | 20.7 | 29.7 | 36.3 | 46.1 | 100 | 291 |
| yolo11n-seg FP16 | GPU | 21.7 | 34.9 | 40.9 | 42.7 | 100 | 263 |
| yolo26n-seg FP16 | GPU | 22.2 | 34.2 | 38.6 | 41.9 | 100 | 268 |
| yolo11s-seg INT8 | GPU | **28.1** | 38.3 | 44.5 | 33.8 | 100 | 283 |
| yolo26s-seg INT8 | GPU | 30.7 | 39.5 | 44.8 | 31.1 | 99 | 286 |
| yolo11s-seg FP16 | GPU | 38.9 | 50.8 | 64.3 | 24.4 | 100 | 266 |
| yolo26s-seg FP16 | GPU | 40.5 | 52.5 | 61.6 | 23.6 | 99 | 269 |
| yolo11n-seg INT8 | **CPU only** | 25.0 | 38.3 | 45.7 | 37.1 | 300 | 252 |
| yolo26n-seg INT8 | **CPU only** | 25.4 | 36.4 | 42.2 | 37.7 | 299 | 259 |
| rfdetr-seg-nano FP16 | GPU | 72.9 | 81.7 | 91.1 | 13.4 | 100 | 246 |
| rfdetr-seg-nano INT8 | CPU only | 94.6 | 102.9 | 107.9 | 10.5 | 382 | 385 |
| rfdetr-seg-small FP16 | GPU | 115.6 | 127.8 | 164.3 | 8.5 | 100 | 242 |
| rfdetr-seg-medium FP16 | GPU | 147.3 | 160.1 | 165.3 | 6.8 | 100 | 267 |

- **Thread-pool bug found and fixed.** With default OpenBLAS/OpenCV threading, the GPU loop burned **729% CPU** (7+ cores spinning) and was slower: p50 28.2 vs 21.7 ms. Forcing one thread fixes both (`runtime.py` header). The daemon must do the same.
- "100% CPU" is the flat-out loop: one core doing pre/post-processing and waiting on the GPU. At a real frame rate CPU use scales down with the frame rate.
- The CPU-only fallback is viable for n-size YOLO INT8: about 25 ms at 3 cores. A machine without a usable GPU still works.

### 3.3 Compositor-side GPU work (`readback.py`, headless EGL, same Mesa iris driver as Hyprland)

| step (1920×1080 window) | p50 ms | p95 ms |
|---|---|---|
| shader downscale to 640×360 + synchronous `glReadPixels` | 3.00 | 3.90 |
| shader downscale to 640×360 + PBO async readback | **2.56** | 2.86 |
| upload 160×160 mask + full-res pixelate pass (with `glFinish`) | **3.63** | 3.96 |

Both steps fit easily in a 16.7 ms frame. The real plugin cost will be lower because it replaces the normal window draw. This is not yet measured inside Hyprland (step P1).

### 3.4 Fail-closed blur latency estimate (from the above)

Readback (≈2.6 ms + 1 frame of async lag) + daemon p50 + mask applied on the next frame:

| config | per change, p50 | p95 | at 60 Hz |
|---|---|---|---|
| yolo11n INT8, single pass | ≈ 40 ms | ≈ 50 ms | 2–3 frames |
| yolo11s INT8, single pass | ≈ 48 ms | ≈ 58 ms | 3 frames |
| yolo11s INT8, 2×2 tiles (4 inferences) | ≈ 130 ms | — | ≈ 8 frames |
| rfdetr-nano FP16, single pass | ≈ 92 ms | ≈ 101 ms | 5–6 frames |
| rfdetr-small FP16, 2×2 tiles | ≈ 480 ms | — | ≈ 29 frames |

The tiled figures assume 4 sequential inferences. Batching the 4 tiles is **not measured**.

---

## 4. Accuracy on COCO person (photos)

### 4.1 Threshold 0.25, dilated mask

| model | mask AP | AP small | hidden small | hidden medium | hidden large | pixel recall | over-blur | false alarm | blurred area on person-free |
|---|---|---|---|---|---|---|---|---|---|
| rfdetr-seg-medium FP16 | 0.489 | 0.205 | **75.4** | **93.3** | **94.9** | 97.4 | 14.4 | 4.6 | 0.19% |
| rfdetr-seg-small FP16 | 0.469 | 0.173 | 70.2 | 92.5 | 94.9 | 97.3 | 14.3 | 5.6 | 0.22% |
| rfdetr-seg-nano FP16 | 0.429 | 0.119 | 61.4 | 90.6 | 94.5 | 97.0 | 14.2 | 4.2 | 0.13% |
| rfdetr-seg-nano INT8 (**CPU**) | 0.427 | 0.119 | 61.3 | 90.4 | 94.4 | 97.0 | 14.4 | 4.0 | 0.17% |
| yolo26s-seg FP16 | 0.469 | 0.221 | 57.9 | 85.7 | 89.9 | 94.8 | 14.8 | 3.8 | 0.19% |
| yolo26s-seg INT8 | 0.458 | 0.217 | 56.5 | 85.2 | 88.1 | 94.0 | 15.2 | 3.6 | 0.09% |
| yolo11s-seg FP16 | 0.446 | 0.198 | 55.7 | 85.1 | 89.5 | 94.4 | 15.2 | 2.4 | 0.11% |
| yolo11s-seg INT8 | 0.444 | 0.196 | 54.5 | 84.8 | 90.2 | 94.6 | 15.3 | 3.0 | 0.13% |
| yolo26n-seg FP16 | 0.416 | 0.162 | 42.9 | 78.8 | 88.0 | 93.0 | 15.2 | 2.6 | 0.22% |
| yolo26n-seg INT8 | 0.407 | 0.156 | 42.3 | 77.9 | 86.5 | 92.5 | 15.6 | 2.6 | 0.29% |
| yolo11n-seg FP16 | 0.398 | 0.149 | 43.5 | 79.8 | 86.6 | 92.6 | 15.6 | 2.8 | 0.31% |
| yolo11n-seg INT8 | 0.397 | 0.147 | 41.9 | 79.5 | 86.6 | 92.8 | 15.7 | 2.8 | 0.29% |

(n = 4308 small, 3723 medium, 2746 large non-crowd person instances.)

### 4.2 A recall-first threshold (0.1)

| model | hidden small | hidden medium | hidden large | false alarm | blurred area on person-free |
|---|---|---|---|---|---|
| rfdetr-seg-medium FP16 | 88.4 | 96.8 | 96.2 | 18.0 | 0.50% |
| rfdetr-seg-small FP16 | 80.3 | 95.9 | 96.1 | 17.6 | 0.58% |
| yolo26s-seg INT8 | 74.4 | 90.9 | 89.8 | 8.6 | 0.37% |
| yolo11s-seg INT8 | 73.0 | 90.7 | 91.7 | 5.2 | 0.17% |
| yolo11n-seg INT8 | 63.6 | 87.1 | 89.3 | 5.6 | 0.42% |

Lowering the threshold gains 8–22 points on small people. False alarms rise to 5–19% of person-free images, but the blurred area stays under 0.6% of the image. For this product that trade is cheap, so **pick the threshold by recall** (as the proposal says).

### 4.3 Render mode (threshold 0.25): raw mask vs dilated mask vs box. Cells are hidden small / medium / large, then pixel recall and over-blur.

| model | raw mask | dilated mask (~1% of long side) | boxes |
|---|---|---|---|
| rfdetr-seg-small FP16 | 24.7 / 69.4 / 86.0, px 94.2, over 8.2 | **70.2 / 92.5 / 94.9**, px 97.3, over 14.3 | 70.6 / 95.9 / 98.5, px 98.9, over 43.6 |
| yolo11s-seg INT8 | 42.1 / 70.5 / 78.8, px 91.6, over 9.0 | **54.5 / 84.8 / 90.2**, px 94.6, over 15.3 | 56.4 / 90.8 / 96.8, px 97.6, over 43.6 |
| yolo11n-seg INT8 | 30.1 / 63.0 / 75.1, px 89.5, over 9.6 | **41.9 / 79.5 / 86.6**, px 92.8, over 15.7 | 44.5 / 86.1 / 95.1, px 96.3, over 44.1 |

- **Raw masks are not usable as the blur region.** Mask edges are off by a few pixels, so only 18–45% of small people end up ≥90% covered. Dilation is mandatory.
- Boxes cover a bit more but triple the over-blur (≈44%). A dilated mask is the right default. Boxes are a sensible fallback for very small instances, as the proposal suggests.

---

## 5. Accuracy on a screen-like window (synthetic 1080p feed)

The plugin sends a whole window, downscaled to the model input. This is the most realistic case measured so far. Threshold 0.25, dilated mask:

| model | pass | hidden small (n=914) | hidden medium | hidden large | pixel recall | over-blur |
|---|---|---|---|---|---|---|
| yolo11n-seg FP16 | full window | 17.8 | 54.3 | 86.0 | 89.1 | 33.2 |
| yolo11n-seg FP16 | 2×2 tiles | 35.2 | 76.1 | 93.5 | 93.6 | 31.4 |
| yolo26n-seg FP16 | full window | 18.1 | 54.2 | 86.1 | 87.6 | 32.7 |
| yolo26n-seg FP16 | 2×2 tiles | 35.6 | 75.7 | 93.2 | 94.5 | 31.4 |
| yolo11s-seg FP16 | full window | 25.9 | 67.3 | 91.8 | 93.5 | 31.7 |
| yolo11s-seg FP16 | 2×2 tiles | **48.0** | **83.3** | 94.5 | 95.5 | 31.5 |
| rfdetr-seg-nano FP16 | full window | 16.4 | 53.0 | 89.1 | 91.2 | 32.2 |
| rfdetr-seg-nano FP16 | 2×2 tiles | 56.3 | 89.3 | 97.2 | 97.9 | 32.2 |
| rfdetr-seg-small FP16 | full window | 21.9 | 62.8 | 92.3 | 93.8 | 32.1 |
| rfdetr-seg-small FP16 | 2×2 tiles | **68.8** | **91.8** | 97.3 | 98.2 | 32.1 |

(Size buckets are measured in window pixels. Over-blur is higher here because a ~19 px dilation around small people is large relative to them.)

- **Per-window inference at 640 is not enough for feed-like pages.** A 1080p window shrinks 3× and photos in it shrink again. Single-pass small-person recall collapses to 16–26%.
- **Tiling is the single biggest lever measured:** it roughly doubles small-person recall (×2–3.4). It costs 4 inferences, plus more if the tiles are batched poorly.
- These are COCO photos pasted into a window, so they are only a proxy. Real screen content (thumbnails, compression, anime, games) is still unmeasured. That needs the screen-domain test set (proposal §9).

---

## 6. Things that broke (and what they mean for the design)

| Finding | Evidence | Consequence |
|---|---|---|
| **Torch and the OpenVINO GPU plugin crash in the same process** (`longjmp causes uninitialized stack frame`) | Reproducible in both import orders | The daemon must be torch-free (it is: `ov_seg.py`). Training/export tools run in separate processes. |
| **IGC crashes on roughly 1 in 3 cold GPU compiles** (segfault/abort inside `libigc.so.2`, no kernel GPU hang) | 21 python core dumps overnight (a few are deliberate torch tests). Core dump frame: `IGC::IgcOclTranslationCtx::TranslateImpl`. Standalone YOLO26n INT8: 1 of 3 cold compiles crashed. | Never compile on the user's machine at runtime. Ship precompiled kernels (`CACHE_DIR` / exported blobs; `bench/warm_cache.sh`). After warming the cache: 0 crashes. Run the daemon supervised and restart it on crash. |
| **RF-DETR INT8 with NNCF's default SmoothQuant collapses** | mask AP 0.000 | Quantize with SmoothQuant off (`quant_rfdetr.py`): AP 0.437 vs FP16 0.446 on 100 images (CPU). |
| **RF-DETR INT8 on GPU: masks empty** (boxes and scores fine) | GPU mask logits all in −288…−39. CPU −107…+19. Box mode at 0.25: 65/95/98 hidden. | RF-DETR INT8 is usable on CPU only: full COCO AP 0.427 vs FP16 0.429, essentially lossless. On GPU it is also slower than FP16, so use FP16 there. Results moved to `results/broken/`. |
| **OpenBLAS/OpenCV thread pools spin 7 cores** | 729% → 100% CPU, p50 28.2 → 21.7 ms | Pin post-processing to 1 thread in the daemon. |

---

## 7. What this changes in the proposal

| Proposal item | Was | Now (measured) |
|---|---|---|
| §1 "Iris Xe speed not measured" | Estimated 20–60 ms | YOLO-n/s INT8: **20–31 ms e2e**. RF-DETR: 73–147 ms. |
| §3 Readback cost | "≤ 2 ms" assumed | **2.6 ms** async (p50). Mask pass 3.6 ms. |
| §4 Fail-closed blur window | 1–4 frames | **2–3 frames** for single-pass YOLO-s INT8. About 8 frames with 2×2 tiles. |
| §5 Boxes vs masks | Dilated mask, box for small | **Confirmed.** Raw masks miss badly. Dilation is mandatory. |
| §6 Model choice | RF-DETR-Seg-N preferred | **On Iris Xe: YOLO11s/26s-seg INT8.** RF-DETR only on faster hardware, or as a slow second pass. |
| §9 Tiling | "add if small recall misses" | **Required** for large windows: small-person recall ×2–3. |
| §11 P0 go/no-go | ≥15 FPS at 640 | **GO** on speed (31–47 FPS). Accuracy on small people is the open risk and goes to P3 (screen-domain fine-tuning). |

### Proposed v1 runtime configuration (changeable)

- Model: **yolo11s-seg INT8** (AP 0.444, 28 ms). Swap in yolo26s-seg INT8 (AP 0.458, 31 ms) if its small-person edge holds on screen data.
- Threshold about **0.1–0.15** (recall-first). Dilated mask, box fallback for instances under about 32 px.
- Full-window pass on every change (fail-closed blur meanwhile) **plus** a 2×2 tiled pass for windows larger than about 1280 px. The tiled pass can run at a lower rate.
- OpenVINO GPU with a precompiled cache. Post-processing on 1 thread. CPU INT8 fallback when the GPU is busy or missing.
- Re-measure on the screen-domain test set before freezing any of this.

---

## 8. Not measured (named, not skipped silently)

| Item | Why not | When |
|---|---|---|
| Power draw | RAPL is root-only. The laptop was on AC with a full battery (`power_now` = 0). | With root, or on battery |
| GPU utilisation % | `intel_gpu_top` needs root | Same |
| Real Hyprland plugin cost | No plugin yet | P1 |
| Real screen content (thumbnails, video, anime, games) | Needs the recorded and labelled screen-domain set | P3 |
| Video / temporal behaviour, tracking, scene cuts | Needs the P2 daemon | P2 |
| Batched 2×2 tiles (one call, batch = 4) | Out of time | Next bench pass |
| YOLO26s / RF-DETR-M in the screen sim | Out of time. The ranking is already clear from COCO. | Next bench pass |

**Interference note:** another session ran Blender EEVEE renders on the same iGPU for most of the night. All accuracy numbers are unaffected by that. All timing numbers in §3 were re-run after the renders finished, and each row is flagged `contended=False`. Earlier contended timings were discarded.

---

## Reproducing

```bash
cd bench
source env.sh                       # user-space Intel GPU runtime, no root
../.venv/bin/python eval.py selftest
../.venv/bin/python export.py       # YOLO + RF-DETR -> OpenVINO IR (FP16/INT8)
../.venv/bin/python quant_rfdetr.py # RF-DETR INT8 (SmoothQuant off)
./warm_cache.sh                     # precompile GPU kernels (IGC is flaky cold)
./run_all.sh                        # accuracy (COCO + screen sim) and timing
./run_runtime.sh                    # daemon-loop timings only
../.venv/bin/python readback.py     # compositor-side GPU cost
../.venv/bin/python summarize.py    # -> results/SUMMARY.md
```

Needs `data/` (COCO val2017 + `instances_val2017.json`) and `.venv` (Python 3.12: openvino, nncf, ultralytics, rfdetr, pycocotools, moderngl).
