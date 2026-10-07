# HaramBlurr — As-Built Log

What we did, **why**, what else we considered, and **what got in our way**. Newest entries at the bottom. One entry per decision or event.
Open problems are tracked in [`issue.md`](issue.md). Details live in the linked documents.

**How to add an entry:** copy the template, fill it in the same day, link the evidence (results file, commit, document section).

```
### YYYY-MM-DD — Short title
- **What:**
- **Why:**
- **Alternatives considered:**
- **What got in the way:**
- **Evidence:**
```

---

## Phase 0: research and tests (Linux first, then Android)

### 2026-10-02 — Started with Linux (Hyprland desktop) as the first platform
- **What:** Designed a filter that sits inside the Linux desktop's screen drawing (a Hyprland plugin plus a background detection program).
- **Why:** On Linux the desktop already holds every window's picture before it reaches the screen, so content could be hidden *before* it is ever shown ("hide first"), with no screen capture.
- **Alternatives considered:** Screen capture + overlay (shows content first), kernel-level (DRM/KMS), per-app layers, writing our own desktop.
- **What got in the way:** The Hyprland plugin API is unstable between versions.
- **Evidence:** [`investigation-linux-v1.md`](investigation-linux-v1.md)

### 2026-10-02 — Benchmarked people-detection models on the laptop (P0)
- **What:** YOLO11/26 (n, s) and RF-DETR (Nano, Small, Medium), FP16 and INT8, on COCO and on a synthetic desktop feed.
- **Why:** Find out whether the laptop is fast enough before writing any app code.
- **Result:** YOLO-s INT8 runs at 31–34 FPS on the Iris Xe. Large people are hidden well; **small people are the main problem**. RF-DETR is more accurate but 3–5× too slow on this GPU.
- **What got in the way:** PyTorch and the OpenVINO GPU plugin crash in the same process; Intel's GPU compiler crashes on about 1 in 3 cold starts; RF-DETR INT8 broke with default settings; thread pools spun 7 CPU cores. All worked around (see results doc §6).
- **Evidence:** [`p0-results-linux-v1.md`](p0-results-linux-v1.md), `bench/results/`

### 2026-10-03 — First phone tests (Redmi 12)
- **What:** Exported the people model to LiteRT (`.tflite`); tested accuracy on synthetic phone screens; started the phone speed test.
- **Result:** The full-size model takes **295 ms** per screen on the phone CPU (4 threads).
- **What got in the way:** The speed test stopped after 2 of ~12 settings and saved nothing (the script only saved at the end). The export also stopped after the 640 px model.
- **Evidence:** [`p0-results-android-v1.md`](p0-results-android-v1.md)

### 2026-10-03/04 — SRS v1.0 (Linux) and two proposal drafts
- **What:** Requirements for the Linux version (English and Arabic); proposal drafts in Arabic.
- **What got in the way:** The two proposal drafts disagreed: one hid **people**, the other "sensitive regions"; both targeted Android while the SRS targeted Linux.

## Phase 0b: moving to Android

### 2026-10-06 — Android first; Linux paused as plan B
- **What:** The team chose Android as the first platform. Linux docs were kept and marked "paused".
- **Why:** The project targets phones (as in the proposal). *(Team: add any other reasons here.)*
- **What got in the way:** On Android a normal app cannot sit inside the screen drawing, so "hide first" is harder (next entry).
- **Evidence:** [`investigation-android-v1.md`](investigation-android-v1.md)

### 2026-10-06 — Target is "people", not "sensitive regions"
- **Why:** All tests so far were about people; "sensitive regions" would need a different model and data. Proposal and cover were aligned.

### 2026-10-06 — Found and fixed broken phone-test tooling
- **What:** The INT8 phone model **found nobody** (0 of 448 detections): boxes (0–640) and scores (0–1) shared one quantization scale, so all scores became 0. The speed-test script lost results on any crash.
- **Fix:** Export now produces fp32, fp16 and dynamic-range files (all checked against fp32); the broken file was moved aside; the speed script saves after every run; the 2 finished results were recovered from the log.
- **Lesson:** Always compare an exported model with the original before measuring its speed.
- **Evidence:** [`p0-results-android-v1.md`](p0-results-android-v1.md) §4

### 2026-10-06 — How the app sees and covers the screen on Android
- **What:** One accessibility service: it hears screen changes, takes a picture of the **app's window only** (Android 14+, at most every 333 ms), and draws covers in a **trusted accessibility overlay**.
- **Why:** A normal "draw over other apps" overlay is capped at **80% opacity** when touches pass through it, so people would show through. Screen capture would include our own covers and asks for permission every session.
- **Alternatives considered:** Screen capture + normal overlay, root, custom ROM.
- **Evidence:** investigation §2, §4, §5; AOSP source

### 2026-10-06 — New order: bad-language text first (v1), then people big → medium → small
- **What:** v1 hides offensive text (Arabic + English); v2 big people, v3 medium, v4 small.
- **Why:** Text needs no AI model at first, is fast, and builds the whole app that later versions reuse. Accuracy on big people is already good; small people need the most work, so they come last.
- **Evidence:** investigation §0, §3; SRS v2.1

### 2026-10-06 — Studied the competitor HaramBlur (extension and Android app)
- **What:** Read the extension's code (ideas only, AGPL-3.0), 163 GitHub issues and 364 Play Store reviews.
- **Result:** Their most common complaint is content showing **before** the blur; also heavy, misses images, asks for permission again; neither product filters text.
- **Decision:** Our differences are hide first without a timeout, bad-language text, covering only the person, every app, and asking for permission once (new NFR-12).
- **Evidence:** investigation §9

### 2026-10-06 — Combined every Arabic bad-word list we found
- **What:** 7 sources → `wordlists/ar_combined.tsv`, 1 906 unique terms (947 in Arabic script), each with its sources.
- **What got in the way:** The first downloads were in a temporary folder that was later deleted, so the sources are now saved in `wordlists/sources/`. Hashtags had to become phrases; one Attia entry was lost by the parser and fixed; Attia's lexicon has no license.
- **Check:** 0 terms lost from any source; self-test passes.
- **Evidence:** [`../wordlists/README.md`](../wordlists/README.md)

### 2026-10-06 — Roadmap and research methods written
- **Evidence:** [`roadmap.md`](roadmap.md), [`research-methods.md`](research-methods.md)

## Phase 0c: the text model and the app design

### 2026-10-07 — We will train our own small text model (v1.1)
- **What:** A second layer after the word list: a small model on the phone that understands context and marks the offensive words.
- **Why:** A word list cannot handle words whose meaning depends on context (كلب، كافر), insults without bad words, or new spellings.
- **Alternatives considered:** Jev (TypeSafe AI): fast "typed decisions", but **cloud only**, which would send screen text to a server; open rivals (Laya, Von, Kev, GLiNER2.5-Decide, Qwen3Guard): useful as **teachers** on the laptop.
- **Evidence:** investigation §3.5

### 2026-10-07 — Choose models by measurement, not by guesswork
- **What:** Only two hard rules (the language is in the model's dictionary; the license allows our use). Everything else is measured on the Redmi 12: **real RAM, ms per message, CPU/GPU**.
- **Why:** The first shortlist (two models) excluded others by assumption; the team asked for measurements instead.
- **What got in the way:** Strong candidates had been missed at first (multilingual-E5-small / MiniLM with only 22 M working parameters; EmbeddingGemma; Gemma 3 270M; classic n-gram models, which won OSACT 2020).

### 2026-10-07 — Language packs, and efficiency beyond shrinking
- **What:** One pack per language (word list + model), one language by default, two if needed; text routed by script. Multilingual models trimmed to one language (vocabulary trimming). Efficiency also from doing less work (cascade, cache, batching, short inputs) and from cheaper kinds of model (n-gram, Model2Vec). Each method measured on its own.
- **Why:** RAM and speed on a low-cost phone matter more than file size.
- **Evidence:** investigation §3.5; research-methods M7; SRS FR-21, NFR-13

### 2026-10-07 — App design agreed
- **What:** Kotlin; one app with one accessibility service; plain-Kotlin text filter; Compose screens; one touch-through overlay; no peeking in v1 (pause only); setup steps for restricted settings and Xiaomi battery; status notification and Quick Settings tile.
- **Why:** Simplest structure that meets the requirements; matches the team's skills.
- **Alternatives considered:** Flutter, Java, Rust for the matcher; separate modules; a separate process for models.
- **Evidence:** [`app-design-v1.md`](app-design-v1.md)

## Phase 1: setting up the project

### 2026-10-07 — Project rule: keep this log up to date
- **What:** Every decision, change, or obstacle gets a dated entry here, in the same piece of work.
- **Why:** This log is the record for the graduation report: what we did, why, and what got in our way.

### 2026-10-07 — Test phone details confirmed
- **What:** Read from the phone over adb: Redmi 12 (model 23053RN02Y), **Android 15** (SDK 35), **HyperOS 2.0**, MediaTek MT6769 (Helio G88), **8 GB RAM** (7.5 GiB usable).
- **Why it matters:** The v2 window-picture method needs Android 14+, so the test phone qualifies. Android 15 also has the stricter "restricted settings" for apps installed from a file (setup step 5 in the app design).
- **Evidence:** `adb shell getprop`; closes issue #2

### 2026-10-07 — Project put in git and on GitHub (private)
- **What:** Git repository with code, docs, word lists and test results; private GitHub repository named after the proposal's English title.
- **Why:** History, backup, and one place for the team.
- **Left out of git:** the Python environment, COCO data, model weights and exports, caches, the Intel GPU runtime, and the phone benchmark binary (large or rebuildable; see the root README).
- **Also:** the "Use of AI tools" note in research-methods §8 was kept, without naming a product or company.

### 2026-10-07 — Full phone speed test (P0b) and 480 px / fp16 accuracy
- **What:** All 6 model files (640 and 480 px; fp32, fp16, dynamic-range) × CPU 1/2/4 threads, CPU with fp16 math, GPU, NNAPI on the Redmi 12 (36 runs); accuracy of the fp16 and 480 px files on the synthetic phone screens.
- **Result:** At 640 px the **GPU is fastest (~205 ms)**; the best CPU setting is **2 fast cores with fp16 math (277 ms)**; **NNAPI gives nothing**. 480 px is faster (~121 ms) but **loses a lot of accuracy** (grid, medium people 64% → 41%), so **we keep 640**. fp16 is as accurate as fp32.
- **Decision:** No setting meets the "≤ 150 ms per full screen" rule at 640, so tiles cannot run on every change: v2 uses the GPU at 640; v3 checks tiles only where the screen changed.
- **What got in the way:** (1) The phone was warm (38–41 °C, on the charger) and the CPU was ~30% slower than on 2026-10-03; re-checked: 301 ms at 37 °C, 357 ms at 38 °C, so it is heat, not a mistake. (2) On the GPU, the 480 px files need **~52–60 s and ~470 MB to start** (640: ~4 s); repeated twice with the same result. (3) The accuracy script only handled 640 px files; it now takes the size from the file name.
- **Evidence:** [`p0-results-android-v1.md`](p0-results-android-v1.md) §2–§4, `bench/results/phone_latency.csv`, `bench/results/phone_tflite_*`; closes issue #6

