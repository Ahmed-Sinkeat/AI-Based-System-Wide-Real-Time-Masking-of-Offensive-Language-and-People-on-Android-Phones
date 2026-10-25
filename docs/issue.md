# Issues

Open problems, risks to check, and decisions still needed. Closed issues stay at the bottom with how they were solved.
Why things were done is logged in [`asbuild.md`](asbuild.md). Streams: **A** Android app · **B** language and data · **C** AI models (see [`roadmap.md`](roadmap.md)).

**Priority:** 🔴 blocks the next step · 🟠 needed soon · 🟢 later or nice to have
**How to add one:** next free number, one row, a clear "next action". When closed, move it to "Closed" with the date and the fix.

---

## Open

### Setup and housekeeping

| # | Pri | Issue | Next action | Stream | Since |
|---|---|---|---|---|---|
| 4 | 🟢 | No short product name yet (the old working name was dropped, C12). Candidate: **Sitr (سِتر)** | Check the Play Store and the web for clashes; team decides before publishing | all | 2026-10-18 |

### People model and phone tests (needed before v3)

| # | Pri | Issue | Next action | Stream | Since |
|---|---|---|---|---|---|
| 30 | 🟢 | GPU start-up at 480 px takes ~52–60 s and ~470 MB (640: ~4 s, ~180 MB) | Only if 480 px is ever used: try the GPU delegate's serialization cache and re-measure | C | 2026-10-07 |
| 7 | 🟢 | Full-INT8 export of the people model is broken (boxes and scores share one scale) | Only if more CPU speed is needed: export with boxes divided by the input size | C | 2026-10-06 |
| 8 | 🟢 | TFLite export stopped after 640 px: 320 px, yolo11n and yolo26s were never exported | Re-run `bench/export_tflite.py` when needed | C | 2026-10-03 |
| 35 | 🟠 | **Drawn people and anime** count as people (SRS 2.8), but the model learned from photos (COCO): domain gap, unmeasured (risk K-9) | v3: add drawn / anime screenshots to the real test set and report them as a separate group; if weaker, add licensed drawn pictures to v5 training | B + C | 2026-10-21 |
| 36 | 🟢 | Are emoji, app icons, stickers and avatars "people"? | Team decision; suggestion: emoji and icons no, stickers and avatars with a human face yes if found. Record it here and in asbuild | all | 2026-10-21 |
| 9 | 🟢 | `bench/yolo26n-seg.onnx` is the **480 px** export (each export overwrites it) | Do not use it as "the 640 model"; name exports by size if it matters | C | 2026-10-06 |

### Text inside images (v2) and video (v6)

| # | Pri | Issue | Next action | Stream | Since |
|---|---|---|---|---|---|
| 31 | 🟠 | **Arabic OCR speed and accuracy on the phone unknown** (P0d) | Week 5: PaddleOCR PP-OCRv5 Arabic + English mobile models on the Redmi 12, CPU and GPU; small meme/thumbnail test set; then set NFR-14 targets | C | 2026-10-18 |
| 32 | 🟢 | No method yet for video (3 window pictures per second cannot follow a playing video) | **After graduation** (v6 is out of the graduation scope): compare tracking, screen capture during video only, strict mode; name it as future work in the report | C | 2026-10-18 |
| 33 | 🟢 | Internet pictures for v5 training must allow this use | Keep a source and license for every downloaded set; prefer openly licensed sets | B | 2026-10-18 |

### Text filter (v1) and word lists

| # | Pri | Issue | Next action | Stream | Since |
|---|---|---|---|---|---|
| 10 | 🟠 | **Attia's lexicon has no license** | Email the author for permission; if no, drop the 239 entries that only come from him | B | 2026-10-06 |
| 11 | 🟠 | **Arabic list needs review:** 947 Arabic-script terms, mostly dialect; context-dependent words (كلب، كافر، حمار، عورة); **no blasphemy entries** | Two people review independently (Cohen's kappa); sort into 4 categories; write blasphemy phrases | B | 2026-10-06 |
| 12 | 🟠 | English list (LDNOOBW) mixes categories and includes neutral or medical words | Review before use | B | 2026-10-06 |
| 13 | 🟠 | **Gap before the cover is not measured** (target ≤ 3 frames) | v1-b: slow-motion filming at 240 fps, ≥ 30 trials per app | A + B | 2026-10-06 |
| 14 | 🟠 | Unknown which apps share their text and **per-letter word boxes** (Chrome is confirmed in its source code; others are not) | v1-a: log what the service sees in Chrome, WhatsApp, Facebook, X, YouTube, Instagram, TikTok | A | 2026-10-07 |
| 15 | 🟠 | The status notification may **stay visible after the app is killed**, so "notification gone = filter stopped" may be wrong | v1-a: kill the process and watch; then a foreground service or a 15-minute health check | A | 2026-10-07 |
| 16 | 🟢 | Do our covers appear in the user's own screenshots? | v1-a: take a screenshot with covers visible | A | 2026-10-07 |
| 17 | 🟢 | Does the overlay slow scrolling (NFR-7)? | v1-a: scroll with the overlay on and off, watch frame drops | A | 2026-10-07 |
| 18 | 🟢 | Restricted-settings steps on HyperOS may differ from stock Android | v1-a: install from a file and follow setup step 5 on the Redmi 12 | A | 2026-10-07 |
| 19 | 🟢 | Play Protect may warn about an app that reads the screen and draws over it | Install early builds from a file and watch for warnings | A | 2026-10-07 |
| 34 | 🟢 | HyperOS may hide or move the **accessibility button** that starts peek (FR-23, risk K-10) | v1-a: request the button on the Redmi 12 and check where it appears; backup: a notification button "show this screen for 10 s" | A | 2026-10-21 |
| 20 | 🟢 | Shared test vectors (Python list builder vs Kotlin app cleaning) not created yet | Create the file when v1-b starts; use it in both test suites | A + B | 2026-10-07 |

### Text model (v1.1)

| # | Pri | Issue | Next action | Stream | Since |
|---|---|---|---|---|---|
| 21 | 🟠 | **Licenses to check** before using: Gemma models (Gemma terms), LFM2 (LFM license), MARBERTv2, AraBERT, ArabicBERT (not stated), HAYAA-student (research only), ArabicDialectSafety and OSACT data | **Checked 2026-10-18** (research-methods §6 table). Still open: ask the authors of AraBERT / ArabicBERT, OSACT and ArabicDialectSafety before shipping a model trained on them; Ultralytics YOLO is AGPL-3.0, so the app must stay open source | B + C | 2026-10-07 |
| 22 | 🟠 | Teachers' Arabic quality unknown (Laya never tested on Arabic; Jev mentions no Arabic) | Week 5: human-checked sample, Cohen's kappa with teacher labels | B + C | 2026-10-07 |
| 23 | 🟢 | Jev / other API terms: may their answers be used to train our model? | Read the terms before using any API teacher | C | 2026-10-07 |
| 24 | 🟢 | Token count for trimming came from a **small sample** (4 276 tokens, 1.7%) | Recount over the full training data per language | C | 2026-10-07 |
| 25 | 🟢 | Real RAM of memory-mapped models may differ from estimates | P0c step 1 measures real RAM per process on the phone | C | 2026-10-07 |

### Research and documentation

| # | Pri | Issue | Next action | Stream | Since |
|---|---|---|---|---|---|
| 27 | 🟢 | "HaramBlur's app uses screen capture" is an **inference**, not confirmed | Keep it labelled as an inference in the report | B | 2026-10-06 |
| 28 | 🟢 | Department reference style unknown (AI-tool use: allowed, C14) | Ask the supervisor; keep IEEE until told otherwise | all | 2026-10-06 |

---

## Closed

| # | Issue | Fixed on | How |
|---|---|---|---|
| C1 | Docs disagreed on platform (Linux vs Android) and target (people vs sensitive regions) | 2026-10-06 | Android first, people as target; Linux docs marked paused; proposal and cover aligned |
| C2 | Phone speed test lost all results when it stopped | 2026-10-06 | `bench_phone.py` saves after every run; 2 rows recovered into `results/phone_latency.csv` |
| C3 | Full-INT8 phone model used for testing found nobody | 2026-10-06 | Moved to `models_tflite/broken/`; export now makes fp32 / fp16 / dynamic-range, all checked against fp32 (open follow-up: #7) |
| C4 | Proposal PDF grew to 2 pages | 2026-10-06 | Student names on one line, shorter goal lines; back to 1 page |
| C5 | Downloaded word lists were lost from a temporary folder | 2026-10-06 | Sources saved in `wordlists/sources/` with their URLs |
| C6 | Model shortlist excluded candidates by assumption | 2026-10-07 | Full candidate list; only two hard rules; choice by phone measurement (P0c) |
| C7 | Project not in git (#1) | 2026-10-07 | Git repository + private GitHub repository; large and rebuildable files ignored |
| C8 | Android version of the Redmi 12 unknown (#2) | 2026-10-07 | Android 15 (SDK 35), HyperOS 2.0, 8 GB RAM: meets Android 14+ |
| C9 | Phone speed test incomplete (#6) | 2026-10-07 | Full run: 34 unique settings (36 saved rows) on the Redmi 12; GPU ~205 ms at 640, best CPU 277 ms, NNAPI useless (p0-results-android §2) |
| C10 | Sustained CPU/GPU benchmark missing (#29) | 2026-10-07 | 15 × 60 s timed blocks per setting, with reload gaps documented: GPU mean 189 ms, CPU 261 ms; CPU block p95 reaches 412 ms. All 30 blocks saved with temperatures (p0-results-android §2.1). App-level sustained/battery tests remain for implementation. |
| C11 | Developer verification (#3) | 2026-10-18 | The team already has a Google Play developer account (published another app on 2026-10-07). ADB installs stay for development. |
| C12 | Working name "HaramBlurr" was too close to the competing "HaramBlur" app (#4) | 2026-10-18 | Name removed from all documents and the folder; the project uses its full title. A short name is still open (#4). |
| C13 | Reasons for Android first not written down (#26) | 2026-10-18 | Written in `asbuild.md` (2026-10-18 entries): reach, where people scroll, phone results good enough for text and big people |
| C14 | AI-tool rules unknown (part of #28) | 2026-10-18 | The department does not forbid AI tools. Kept the use-of-AI note in research-methods §8; no AI tool is named as an author or co-author. |
| C15 | Old proposal draft `docs/ha.pdf` (#5) | 2026-10-18 | Removed from the repository (it carried the old working name); still in git history. The current proposal is `Initial-Project-Proposal.pdf`. |
