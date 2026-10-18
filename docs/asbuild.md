# As-Built Log

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
- **Why:** The project targets phones (as in the proposal). More reasons are written in the 2026-10-18 entry "Why Android, and why on the phone".
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

### 2026-10-07 — Completed the sustained phone benchmark and checked the handoff
- **What:** On the connected Redmi 12, ran the 640 fp32 model for 15 consecutive 60-second blocks on CPU (2 threads, XNNPACK fp16), then 15 on GPU (OpenCL). Saved raw logs and a 30-row CSV with timing, memory, temperature and charging state; removed the temporary model from the phone afterwards.
- **Why:** Close the remaining P0b heat/performance follow-up (#29), without repeating unchanged model exports or expanding into the deferred candidates.
- **Result:** 8 165 timed inferences. GPU weighted mean **189.3 ms**, CPU **261.4 ms**. CPU warmed from 34 to 40 °C and its final block's **p95 reached 411.9 ms**; GPU ran at 38–41 °C with no progressive slowdown. **The 150 ms target remains unmet.** GPU stays the people-model choice.
- **Limits:** AC charging throughout; GPU followed CPU without cooling. Each block reloads the model (CPU ~0.1 s, GPU ~3–4 s), so this is near-continuous load rather than a persistent interpreter. App-level latency and battery life still need the implementation.
- **Checks:** All 30 blocks complete, no benchmark errors or delegate fallback, each configured for 60 seconds with paired battery readings. Metric and word-list self-tests pass; Python compilation passes; word-list rebuild is byte-for-byte unchanged. Audited the six existing valid accuracy reports (60 screens per layout each), without re-running them.
- **Correction:** The previous speed CSV contains **34 unique valid settings**, not 36: dynamic-range files skip fp16 math. Its 36 rows include two earlier repeats; the results report now states that distinction.
- **Evidence:** [`p0-results-android-v1.md`](p0-results-android-v1.md) §2.1, [`raw log`](../bench/results/phone_sustained_2026-10-07.log), [`CSV`](../bench/results/phone_sustained_2026-10-07.csv); closes issue #29. Optional exports (320 px, YOLO11n, YOLO26s), 480 GPU cache work and future text/app tests remain deferred.

## Phase 1b: name, scope and six-month plan

### 2026-10-18 — Working name dropped; project uses its full title
- **What:** Removed the working name "HaramBlurr" from all documents, the requirements, the app design and the test logs. The project is now called by its full title: *AI-Based System-Wide Real-Time Masking of Offensive Language and People on Android Phones*. The project folder is renamed to `android-masking/`. The old draft `docs/ha.pdf` (which carried the old name) was removed.
- **Why:** The name was one letter away from the competing "HaramBlur" extension and app (~700K installs), which would confuse users and examiners. "HaramBlur" stays only where we cite it as prior work.
- **Alternatives considered:** Keep the name; pick a new short name now. A short name is left open; candidate **Sitr (سِتر)** (issue #4).
- **Also:** In the raw phone log `bench/results/phone_sustained_2026-10-07.log` the temporary model path on the phone was renamed from `/data/local/tmp/haramblurr_sustained_640_fp32.tflite` to `/data/local/tmp/masking_sustained_640_fp32.tflite` (60 lines, text only; no numbers changed). Older entries above keep the old wording as history.
- **Evidence:** closed issues C12 (name) and C15 (`ha.pdf`, #5)

### 2026-10-18 — Why Android, and why on the phone (not the cloud)
- **What:** Confirmed: Android first (PC/Linux stays paused as plan B), and all AI runs on the phone. The app has no internet permission.
- **Why Android:** It is where people scroll (social media, short videos), so the filter helps more people. Phone test results are good enough for text and big people (GPU ~189–205 ms per screen); small people are hard on any hardware, so a PC would not solve the hard part.
- **Why on the phone:** Privacy (screen pictures never leave the phone), works without internet, no mobile data cost, no server bill or subscription to run. Large models are used only while **training** (laptop or Colab), then shrunk for the phone.
- **Alternatives considered:** PC app (more power, but less used for scrolling); cloud models (stronger, but sends every screen to a server, costs money each month, needs user accounts and data protection).
- **Evidence:** [`p0-results-android-v1.md`](p0-results-android-v1.md), [`investigation-android-v1.md`](investigation-android-v1.md) §0; closes issue #26 (C13)

### 2026-10-18 — Why a window picture, not screen casting
- **What:** Kept the accessibility service window picture (`takeScreenshotOfWindow`, Android 14+) as the only way to see images. Screen casting (MediaProjection) is not used.
- **Why:** (1) Allowed once in settings; casting asks again every session on Android 14+. (2) The window picture does **not** include our own covers, so we can cover first and check under the cover; casting sees our covers (flicker). (3) The model handles about 5 pictures per second, so casting's 60 frames per second would be wasted work. (4) Our covers stay fully opaque in the trusted accessibility overlay; normal overlays are capped at 80% opacity. Memory: one picture at a time, nothing saved to storage.
- **Limit:** At most one picture per window every 333 ms, so a playing video cannot be followed this way (planned for v6).
- **Evidence:** [`investigation-android-v1.md`](investigation-android-v1.md) §2, §4, §5

### 2026-10-18 — New release order and six-month plan
- **What:** The deadline is about six months away (about mid-April 2027; week 1 = Mon 12 Oct 2026). New order: **v1** bad-language text → **v1.1** our own small text model → **v2** bad words in text **inside images** (on-phone OCR) → **v3** big people → **v4** medium → **v5** small (own fine-tuned model) → **v6** people in videos. Roadmap rewritten for 27 weeks; SRS updated to **v2.2** (new FR-12 text in images, FR-19 video, NFR-14 OCR targets after test P0d).
- **Why:** Text inside images reuses the text filter and is cheaper than people, so it comes before them. Video is the hardest (needs more than 3 pictures per second), so it is last.
- **Also decided:** Hide the **whole person**, with no gender guess. Building our own small-people model by fine-tuning is in scope (v5).
- **Evidence:** [`roadmap.md`](roadmap.md), [`srs-en.html`](srs-en.html), issues #31–#33

### 2026-10-18 — Scope limits and project facts
- **What:**
  - **Android 14+ only** for picture features; older phones are not supported for now. The Android 13 screen-casting fallback (FR-16) is dropped.
  - **Banking and other secure apps are not promised** (they block screenshots; there is no need to filter them). FR-15 marked "by design".
  - **v5 training data is private and never published**, plus openly licensed internet pictures (license kept for each set, issue #33).
  - The team **already has a Google Play developer account** (another app published on 2026-10-07). APK installs during development, then Google Play.
  - **AI tools are allowed** by the department. No AI tool is named as an author or co-author in commits, documents or the report.
- **Evidence:** SRS v2.2 §3, §4; [`research-methods.md`](research-methods.md) §8; closes issues #3 (C11) and the AI part of #28 (C14)

### 2026-10-18 — Graduation scope: v1 to v4; v5 bonus; v6 after graduation
- **What:** The graduation project is **v1 to v4** (bad-language text, our own text model, text inside images, big and medium people). **v5** (small people) is a **bonus**, started only when v4 meets its exit criterion. **v6** (video) moves to **after graduation** and appears in the report only as future work. Roadmap re-planned: v4 gets Weeks 13–15, a new "test v1–v4 together" phase in Weeks 16–18, v5 (bonus) Weeks 17–22, report and defense Weeks 22–27.
- **Why:** Six months for three people is tight for seven versions. v5 needs our own data and training, and v6 needs a method that does not exist yet; both could eat the time needed to finish and test v1–v4 well. v1–v4 already make a complete product: text everywhere plus people the model finds reliably.
- **Alternatives considered:** Keep v1–v6 in scope (risk of four half-finished versions); drop v5 completely (loses the part with the most research value if time allows).
- **Also:** A team-only guide and the supervisor slides live in `private/` (ignored by git).
- **Not yet updated:** SRS v2.2 (`srs-*.html` / `.pdf`) still lists v5 and v6 as planned versions.
- **Evidence:** [`roadmap.md`](roadmap.md); issue #32

### 2026-10-18 — v1.1 merged into v1
- **What:** Our own small text model is now part of **v1** (layer ② next to the word list), not a separate version "v1.1". v1 runs Weeks 1–9; the word list and app (part 1) and the model (part 2) are built in parallel as before. Version numbers v2 to v6 do not change.
- **Why:** The model is a small piece of the same text feature; a separate version number made the scope look bigger and split one feature in two.
- **Not yet updated:** older documents (investigation, app design, research methods, SRS, issues) still say "v1.1"; read it as "v1, layer ②".
- **Also:** the supervisor slides were rewritten: less technical detail, no week numbers (only the order of work), more on **why** each method was chosen and why we cover before checking; HaramBlur is described as both a browser extension and an Android app.
- **Evidence:** [`roadmap.md`](roadmap.md)

### 2026-10-18 — Team guide and supervisor slides in English and Arabic
- **What:** The team guide in `private/` is now a designed page with drawn diagrams, in **English and Arabic** (`team-guide-en/ar.html` + `.pdf`, Arabic right-to-left). It explains the whole app as a process (what happens when you scroll, every part of the app, how text and images share the phone) without deep technical detail, and adds a **machine-learning learning path** tied to our versions. The supervisor slides are built in both languages from one script (`build-deck.js en|ar`, Arabic mirrored right-to-left).
- **Why:** The team asked for a simple explanation of the whole process and a way to learn ML for the project; the supervisor and the team read both languages.
- **Slides cut to 6 + backup:** the proposal was already given to the supervisor, so the meeting is a follow-up. Main slides: title, what we did since the proposal, scope to approve, how it works (cover first), evidence, plan + decisions we need. Problem and idea slides removed (in the proposal); the detailed slides stay after the end as backup for questions.
- **Proposal written into the guide (not yet in app design):** people model on the graphics chip and the text-in-image reader on the main processor, one image job at a time, latest screen wins. To be measured in v2/v3.
- **Evidence:** `private/` (not in git)

### 2026-10-18 — Research and related-work page (HTML + PDF)
- **What:** Wrote [`research-en.html`](research-en.html) (+ `research-en.pdf`, 16 pages): research questions, methods, a full related-work review in 9 topics (offensive language, Arabic, small phone models, OCR, people segmentation, hiding images, Android platform, existing products, gap table), findings so far, evaluation plan, validity, ethics. Added 25 new references [71]–[95] to [`research-methods.md`](research-methods.md) §9 so numbers match.
- **Why:** The research was done but the related-work chapter was not written; this is the base for the report's background chapter and something readable to show the supervisor.
- **Alternatives considered:** Arabic version too (skipped for now, English only); a separate reference list (rejected, numbers would drift).
- **What got in the way:** One survey (Husain & Uzuner, TALLIP) could not be verified and was left out. SafeGaze features were not tested, so they are marked "not checked".
- **Evidence:** [`research-en.html`](research-en.html) §4, references.

### 2026-10-18 — Decision models added to the related work
- **What:** [`research-en.html`](research-en.html) §4.3 now covers "decision models" (Jev and open alternatives, refs [49]–[53]); §4.4 says text read from images goes through the same text model.
- **Why:** The typed answer of our v1 text model and its teachers come from this idea, but the page did not say so. People are not done this way: a decision model gives a label for the whole image, and we need each person's shape to cover only the person.
- **Alternatives considered:** Using Jev in the app (rejected: cloud only, screen text would leave the phone).
- **What got in the way:** Nothing.
- **Evidence:** [`investigation-android-v1.md`](investigation-android-v1.md) §3 (typed answer, teachers).
