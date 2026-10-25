# Research Methods and References

Graduation project, Software Engineering · Date: 2026-10-06, updated 2026-10-18 · Status: living document (updated after each phase)
Related: [`roadmap.md`](roadmap.md) · [`investigation-android-v1.md`](investigation-android-v1.md) · [`p0-results-android-v1.md`](p0-results-android-v1.md) · [`p0-results-linux-v1.md`](p0-results-linux-v1.md)

References use IEEE style. Numbers in square brackets point to §9.

---

## 1. Purpose and scope

The project builds an Android app that hides offensive language and images of people on the phone screen, across apps (system-wide), on the device itself. This document records **how the research was done**: what questions it asks, which methods answer them, what data and tools were used, and what the limits are. It covers the work done so far (research, tests, competitor study, word-list building) and the planned evaluation of each release (v1 text, v1.1 text model, v2 text inside images, v3–v5 people, v6 video).

---

## 2. Research questions

| ID | Question |
|---|---|
| **RQ1** | Can a normal (not rooted) Android app hide offensive text and images of people in every app, without first showing them to the user? What are the platform limits? |
| **RQ2** | How well does a word-list method with Arabic text normalization find offensive Arabic and English words on screen, and how many normal words does it cover by mistake? |
| **RQ3** | How fast and how accurate are real-time person-segmentation models on a low-cost phone, for people of different sizes on the screen? |
| **RQ4** | What problems do users report with existing tools, and which of them can a different design avoid? |
| **RQ5** | Can a small model that runs on a low-cost phone, trained with labels from large open models ("teachers"), find offensive Arabic and English messages **and the offensive words in them** better than a word list, within the phone's speed and size limits? |
| **RQ6** | Can on-phone OCR read Arabic and English text inside images fast enough to cover the offensive words in it? |

---

## 3. Research design

The project follows an **engineering design research** approach: build an artifact (the app) in stages, and evaluate each stage against measurable requirements (SRS v3.0). Several methods feed into it:

| # | Method | Answers | Status |
|---|---|---|---|
| M1 | Literature and technical documentation review | RQ1, RQ2, RQ3 | Done, updated as needed |
| M2 | Source-code analysis (Android, Chromium, a competitor) | RQ1, RQ4 | Done |
| M3 | Competitor and user-feedback analysis | RQ4 | Done |
| M4 | Controlled offline experiments with person-segmentation models (laptop and phone) | RQ3 | Done (phone speed test partly) |
| M5 | Lexicon construction: combining and normalizing Arabic offensive-word lists | RQ2 | Done (combined list); manual review planned |
| M6 | Evaluation of each release on the test phone | RQ1–RQ3, RQ6 | Planned (v1 → v6) |
| M7 | Training and evaluating our own on-device text model (teacher → student) | RQ2, RQ5 | Planned (v1.1) |

---

## 4. Methods

### 4.1 M1 — Literature and technical documentation review

**Goal.** Find what the platform allows (RQ1), what is known about Arabic offensive-language detection (RQ2), and which models suit real-time use on weak hardware (RQ3).

**Sources searched.** Web search engines; the ACL Anthology and arXiv for papers; official Android developer documentation and Android source code (AOSP); Chromium source code; model and library repositories (GitHub, Hugging Face); app stores.

**Procedure.**
1. Search with targeted queries (for example: Android accessibility screenshot API limits; overlay touch and opacity rules; Arabic offensive language datasets and word lists; Arabic OCR on device; real-time segmentation on mobile).
2. Prefer **primary sources**: official documentation, source code, the paper itself. Secondary sources (blogs, summaries) are used only as leads.
3. **Verify important facts at the primary source** before using them in the design. Examples:
   - The accessibility screenshot rate limit was read from the AOSP source on four branches: 1000 ms on Android 11, 333 ms on Android 13, 14 and current [28].
   - The 80% opacity cap for see-through overlays was read from the AOSP commit [29].
   - Chrome's support for per-character text boxes was confirmed in Chromium's source [34].
   - Citation details (authors, pages, DOIs) were taken from ACL Anthology BibTeX and the arXiv API.
4. Record each source with its URL and access date (§9).

**Main findings used in the design.** Summarized in the investigation, §2 (platform options), §3 (text), §4–§5 (people, hide first), §8 (limits), §11 (resources). In short:

- **Android platform (RQ1).** An accessibility service can read on-screen text and draw trusted overlays [25]. Since Android 8.0 it can ask for the screen box of each character [26], and Chrome supports this for web pages [34]. Android 14 added screenshots of a single window and new overlay methods [27], limited to one screenshot per 333 ms [28]. Normal "draw over other apps" overlays that let touches through are capped at 80% opacity [29], [30]. Screen capture (MediaProjection) needs user consent for every session on Android 14+ [31], and attempts to hide an app's own overlay from screen capture failed on a MediaTek phone [36]. Google Play restricts non-accessibility uses of the accessibility API [32]. The official codelab [35] and an open-source accessibility app with overlays and OCR [40] serve as implementation references.
- **Arabic offensive language (RQ2).** Word lists built from social media exist [1], [6], [20]–[24]; shared tasks and studies show that Arabic letter normalization and reducing repeated letters help detection [2]–[4]; Arabizi needs its own handling [5]. Normalization follows Lucene's `ArabicNormalizer` [17]; many phrases can be matched in one pass with Aho-Corasick [18]. A small distilled Arabic toxicity model exists for on-device use [15], and could serve as a second check.
- **Text inside images (v2).** Google's on-device OCR (ML Kit) does not support Arabic [33]; PaddleOCR has an Arabic mobile model [16], and it already runs on Android in an open-source app [41].
- **People detection (RQ3).** Candidate real-time models were YOLO segmentation models [10] and RF-DETR [8], [11], [48]; SAM 3 [9] can label people from a text prompt to build training data. COCO [7] is the standard benchmark.
- **Related tools (RQ4).** HaramBlur (browser extension and Android app) [37], [38] and SafeGaze [39] blur images; none filters text.
- **Linux phase (plan B).** Per-window shader plugins for the Hyprland desktop [43], [44], its rendering pipeline [46] and a planned Vulkan renderer [45]; YOLO with OpenVINO on an integrated GPU [47].

**Limits.** Web search results change over time and depend on the search engine. Some sources are company blogs or store pages. Where a claim could not be confirmed at a primary source, the documents say so (for example, whether a competitor uses screen capture).

### 4.2 M2 — Source-code analysis

**Goal.** Learn how existing software actually behaves, beyond what its documentation claims.

| What | Version read | Question | Result |
|---|---|---|---|
| AOSP `AccessibilityService.java`, `AbstractAccessibilityServiceConnection.java` [28] | branches android11, android13, android14, master | How often may an accessibility service take a screenshot? Per window or per display? | 333 ms per window (Android 13+); 1000 ms on Android 11 |
| AOSP commit a451d5b [29] | — | Can an app overlay be opaque and let touches through? | No: capped at 80% opacity |
| Chromium `WebContentsAccessibilityImpl.java` [34] | main branch | Does Chrome give per-character boxes to accessibility services? | Yes |
| HaramBlur browser extension [37] | commit f47000e (July 2024), 2 159 lines of JavaScript | How does a competitor detect, hide, and handle timing? | Whole-image blur; nsfwjs + face/gender model; optional "blurry start" with a 7 s timeout; no text filtering (investigation §9) |

**Procedure.** Clone or download the source at a fixed version, read the relevant files, and note the exact lines and constants. The competitor's code is licensed AGPL-3.0: it was **read for ideas only, not copied**.

### 4.3 M3 — Competitor and user-feedback analysis

**Goal.** Find the real problems users have with existing tools (RQ4).

**Data.**

| Data | Collection | Size |
|---|---|---|
| GitHub issues of the HaramBlur extension [37] | GitHub REST API, all open and closed issues (pull requests excluded), 2026-10-06 | **163 issues** (90 open, 73 closed), Oct 2023 – Jul 2026 |
| Google Play reviews of the HaramBlur Android app [38] | `google-play-scraper` [19]: newest 200 reviews each for English/US, Arabic/Egypt, Arabic/Saudi Arabia, duplicates removed, 2026-10-06 | **364 reviews**, 14 Jun – 5 Oct 2026; 44 with 1–3 stars |
| Store metadata [38] | Same tool | ~696 000 installs; 4.61 stars from 14 667 ratings; released 17 Nov 2025; in-app purchases $3.99–$34.99 |
| The team's own use of the app | Informal use by a team member | Three problems: feels heavy, misses images, asks for permission again |

**Analysis.**
1. Read all issues and all 1–3 star reviews in full.
2. **Thematic coding**: group complaints into themes (delay before blur, misses, wrong blur, heavy, permissions, limited apps, cost, no text filter).
3. Count how often each theme appears using English and Arabic keyword patterns, then check the matches by reading them, and remove false matches (for example, "men" inside "recommend").
4. For each theme, record the design answer (investigation §9, "Known problems").

**Limits.** Keyword counts are approximate. Only the newest reviews in three language/country settings were collected, so older reviews and other countries are missing. Reviews are self-selected (unhappy and very happy users write more). The team's own use is informal, not a controlled test. The claim that the competitor uses screen capture is an **inference** from its behaviour, not a confirmed fact.

**Ethics.** Only public data was used. Reviews and issues are reported in aggregate and quoted without user names.

### 4.4 M4 — Controlled experiments with person-segmentation models

**Goal.** Measure speed and accuracy of candidate models for hiding people (RQ3), before writing app code.

**Hardware.**
- Laptop: Intel Core i5-1135G7, Intel Iris Xe integrated GPU, 7.5 GiB RAM, Arch Linux.
- Phone: Xiaomi Redmi 12 (4G), MediaTek Helio G88 (2 × Cortex-A75 + 6 × Cortex-A55), Mali-G52 MC2 [42].

**Software.** Python 3.12; OpenVINO 2026.4.1 and NNCF 3.4.0 [12]; Ultralytics 8.4.171 [10]; rfdetr 1.11.1 [11]; onnx2tf 2.6.9 [14]; ai-edge-litert 2.1.2 and LiteRT `benchmark_model` [13]; ONNX Runtime 1.26.0; OpenCV 4.13; pycocotools 2.0.11.

**Models.** YOLO11n/s-seg and YOLO26n/s-seg [10]; RF-DETR-Seg Nano/Small/Medium [8], [11]; each in FP16 and INT8 (laptop), and fp32 / fp16 / dynamic-range (phone).

**Data.**

| Test set | Built from | Size |
|---|---|---|
| COCO person (photos) | COCO val2017 [7] | 2 693 images with people (10 777 person instances) + 500 person-free images |
| Synthetic desktop window | COCO photos pasted into a 1920 × 1080 feed-like window | 100 windows, 2 320 people (914 small, 807 medium, 599 large) |
| Synthetic phone screens | COCO photos in 1080 × 2340 screens: "feed" (full-width posts) and "grid" (3 columns) | 60 + 60 screens; 473 and 3 670 people |
| Calibration (INT8) | coco128 (Ultralytics) | 100 images for the phone export |

**Metrics.**
- **Hidden**: a person counts as hidden when at least **90% of their pixels** are under the cover. Reported per size bucket (COCO areas: small < 32², medium < 96², large ≥ 96² pixels).
- **Pixel recall**: share of all person pixels covered. **Over-blur**: share of covered pixels that are not a person. **False alarm**: share of person-free images with any cover.
- Confidence thresholds 0.1, 0.25, 0.4 and 0.5. The cover is the predicted mask dilated by about 1% of the image's long side.
- Speed: median (p50), p95 and p99 latency; CPU use; memory.

**Procedures.**
1. **Laptop speed**: OpenVINO `benchmark_app` (batch 1, latency mode) and a full detection loop (`bench/runtime.py`, 30 s per model).
2. **Laptop accuracy**: all models on COCO person and the synthetic window, single pass and 2 × 2 tiles (`bench/eval.py`).
3. **Phone-screen accuracy**: the same model family on the synthetic phone screens, whole screen and 3 vertical tiles with 64 px overlap (`bench/phone.py`).
4. **Phone-file validation**: the exported `.tflite` files were run on the laptop with LiteRT on the same phone screens (`bench/phone_tflite.py`), and each variant was compared with the fp32 file on 40 held-out images (person detections with score ≥ 0.25 kept). **This step found that the full-INT8 file finds nobody** (0 of 448 detections), because boxes and class scores share one quantization scale. The file was removed from the phone tests.
5. **Phone speed**: LiteRT `benchmark_model` over adb, 10 warm-up and 60 timed runs per setting, a 20 s pause between runs against heat, battery temperature recorded (`bench/bench_phone.py`). Only 2 of about 12 settings finished before the run stopped. The script now saves after every run.

**Results.** [`p0-results-linux-v1.md`](p0-results-linux-v1.md) and [`p0-results-android-v1.md`](p0-results-android-v1.md).

**Limits.** The test screens are synthetic (COCO photos placed on screens), not real app screenshots. COCO contains mostly real photos, so drawings, anime and game characters are under-represented. Phone accuracy was measured on the laptop with the phone's model file, which gives the same detections but not the phone's speed. Phone speed so far covers only fp32 on the CPU.

### 4.5 M5 — Lexicon construction (Arabic offensive words)

**Goal.** Build a starting word list for v1 (RQ2) from all openly available Arabic lists.

**Sources** (all downloaded 2026-10-06, kept unchanged in `wordlists/sources/`):

| Source | Entries | License |
|---|---|---|
| LDNOOBW V2, Arabic [21] | 1 284 | CC0 |
| Mubarak et al. 2017 obscene words and hashtags [1] | 415 | Research use |
| Attia 2025 categorized lexicon [6] | 371 | None stated (permission to be requested) |
| profanity.csv, Arabic [23] | 48 | MIT |
| LDNOOBW (first version), Arabic [20] | 38 | CC-BY-4.0 |
| uxbertlabs list [22] | 16 | MIT |
| cuss, Arabic in Latin letters [24] | 245 | MIT |

**Procedure** (`wordlists/build_ar.py`):
1. Parse each source. Attia's lexicon is a document, so terms are taken from its bullet entries together with his category heading.
2. **Normalize** each term with the rules of Lucene's `ArabicNormalizer` [17]: remove diacritics (tashkeel) and tatweel; أ إ آ ٱ → ا; ى → ي; ة → ه. Also lowercase Latin letters, and turn hashtag and joining signs (`#`, `_`, `-`, `.`) into spaces, because screen text is split into words.
3. **De-duplicate** on the normalized form, and keep the **provenance** of every term (which lists contain it), so any source can be removed later.
4. Map Attia's eight categories to ours (swearing, sexual, insult) as a **suggestion**. No source has a blasphemy category.
5. **Verify** that no term is lost: every normalized input term from every source must appear in the output (result: 0 missing). A self-test checks the normalizer and the parsers (`python3 build_ar.py --test`).

**Result.** 1 906 unique terms: 947 in Arabic script (680 single words, 267 phrases) and 959 in Latin script (Arabizi). 147 Arabic terms appear in two or more lists.

**Planned manual annotation (step v1-c).**
- Two team members **independently** label every Arabic-script term: keep for v1 (standard Arabic) or later (dialect); category (swearing / sexual / insult / blasphemy); and "context-dependent" (a normal word in other contexts, such as كلب or كافر).
- Measure agreement with **Cohen's kappa** on all terms, then settle disagreements by discussion. Report kappa in the results.
- Write the blasphemy phrases as a team, since no source contains them.

**Limits.** Most sources come from social media and mix dialects (mainly Egyptian, Levantine and Gulf). Some lists were built automatically, partly with an LLM (Attia). Word lists cannot see context, which is why context-dependent words are kept only inside phrases.

### 4.6 M6 — Planned evaluation of each release

Each release is measured against the SRS v3.0 targets on the test phone. Results go into a results document per release.

**v1 (bad-language text)**

| Measure | Method | Target |
|---|---|---|
| Recall on offensive words (NFR-1) | Test sets: the OSACT 2020 offensive-language tweets [2] (test split), plus English comments and our own screenshots. The team marks the offensive words in a sample; we measure the share that the app covers. Report with a 95% confidence interval (Wilson). | ≥ 95% |
| False covers (NFR-2) | Clean text: news articles, Quran text, schoolbook pages, normal chats. Count covers per 1 000 words. | ≤ 1 |
| Gap before the cover (NFR-3) | Film the test phone with a second phone in slow motion (240 fps) while new text appears; count frames until the cover appears. At least 30 trials per app, in at least 5 apps. Cross-check with timestamps logged by the app. | ≤ 3 screen frames (≈ 33 ms at 90 Hz) |
| Battery (NFR-8) | Reset battery statistics (`dumpsys batterystats --reset`), then 30 minutes of scripted scrolling with the filter on and off, 3 times each | Small difference (report the value) |
| App coverage | List of popular apps where the text is readable and the word boxes work | Report |

**v2 (text inside images)**

| Measure | Method |
|---|---|
| OCR speed and memory (P0d) | PaddleOCR mobile models on the Redmi 12, CPU and GPU, as in M4: ms per screen, peak RAM, warm phone |
| Hidden words in images (NFR-14) | Real screenshots with text in images (memes, thumbnails, video subtitles); the team marks offensive words; share covered, with a 95% confidence interval |
| Waiting time | App timestamps: change event → window picture → OCR → cover |

**v3–v5 (people)**

| Measure | Method |
|---|---|
| Hidden people by size (NFR-4) | Test set of real phone screenshots (feeds, grids, video apps, games), people labelled with SAM 3 [9] and checked by hand; same "hidden" metric as M4 |
| Waiting time (NFR-5) and check speed (NFR-6) | App timestamps: change event → window picture → model result → cover removed; p50 and p95 |
| Exposure | Slow-motion filming as for v1: frames in which a person is visible before the cover |
| Over-cover, battery, memory | As in M4 and v1 |

**v6 (video).** Share of video seconds in which a person is visible, measured by slow-motion filming; compared across the methods in the roadmap (tracking, screen capture during video, strict mode).

**v5 training data.** Phone screenshots collected by the team, plus openly licensed pictures from the internet (source and license recorded per set), labelled with SAM 3, a sample checked by hand, and **split by app and by screenshot session** so that test images are not near-copies of training images.

### 4.7 M7 — Training and evaluating our own on-device text model (v1.1)

**Goal.** Answer RQ5: build a small text model for the phone that understands context and marks the offensive words, and compare it fairly with simpler and larger options. Design: investigation §3.5.

**Background.** "System One" decision models such as Jev [49] return a fixed, typed answer with a confidence instead of free text, but Jev runs only as a cloud API. Open alternatives exist [50]–[53]; guard models such as Qwen3Guard [54] cover 119 languages, and FanarGuard [59] adds Arabic cultural context. Their memory and speed on the test phone are estimated from their parameter counts and **measured** before any choice (step P0c below). Most of a multilingual model's parameters sit in its word table; **vocabulary trimming** removes the tokens a language never uses and keeps the model's performance without retraining [63]. Small fine-tuned encoders can match or beat large generative models on narrow Arabic safety tasks [56], [57], and a distilled Arabic toxicity model keeps 96.7% agreement with a teacher 68× larger [15]. Finding *which words* are offensive is the toxic-spans task [60].

**Data.**

| Set | Source | Use |
|---|---|---|
| Arabic offensive tweets | OSACT 2020 [2], Mubarak 2017 [1] | train / dev / test |
| Arabic safety texts, standard-Arabic part | ArabicDialectSafety [56] | train / test (check its license first) |
| List-matched sentences | Sentences that contain entries of our combined list (M5) | train (hard cases with context-dependent words) |
| Clean text | News, Quran, schoolbooks, normal chats | negatives, false-cover test |
| English | Comments with and without listed English words | train / test |

The **test set is fixed before training** and never used for choosing settings.

**Teacher labelling.**
1. Two or more large open models run offline on the laptop or Colab: Qwen3Guard-8B [54] and Laya [51]. A cloud model (Jev [49] or similar) is used only if its terms allow using its answers to train another model.
2. Each text gets the same **typed questions**: offensive (yes/no + confidence)? category (clean / swearing / sexual / insult / blasphemy)? which words?
3. Labels are combined by **majority vote**. Texts where the teachers disagree are sent to human review.
4. Two team members label a random sample independently; we report **Cohen's kappa** between the humans, and between humans and the combined teacher labels.

**Language packs.** Each language (Arabic, English) is a separate pack with its own word list, tokenizer, model and thresholds; the user enables one (default) or two (FR-21). Text is routed to a pack by its script. Every step below is done **per language**, and different languages may end up with different models.

**Candidates.** Selection uses only two hard rules: the language must be in the model's dictionary, and the license must allow our use. All other candidates are measured. The list (investigation §3.5) covers: a classic character n-gram linear model, as used by the OSACT 2020 winner [64]; static-embedding models (Model2Vec [65], [66]); tiny Arabic encoders; small multilingual encoders (multilingual-E5-small / MiniLM [69], mmBERT-small [55]); Arabic and multilingual base encoders (CAMeLBERT [62], MARBERTv2 [61], Laya-multilingual [51], EmbeddingGemma [67]); and small generative models (Gemma 3 270M [68], Qwen3Guard-Stream-0.6B [54]). Models with English-only dictionaries are dropped by the first rule. Multilingual models are first **trimmed to the pack's language** [63]; a first count on a small sample used 4 276 distinct Arabic + English tokens (1.7% of a 256 000-token dictionary).

**Step P0c: choose each pack's model by measurement, in two steps.**
1. **Phone test (no training needed):** export each trimmed candidate to LiteRT and run it on the Redmi 12 with the same procedure as M4: **real RAM of the process** (not file size, because LiteRT memory-maps model files [70]), **p50/p95 ms per message at 16, 32 and 64 tokens, CPU with 1/2/4 threads and GPU**, battery temperature. Candidates that miss NFR-13 (real RAM ≤ 100 MB, ≤ 50 ms p95, about one CPU core at most) stop here.
2. **Quality test:** quick fine-tuning of the remaining candidates on a small development set per language; F1 and false covers decide.

**Student.** The winner of P0c for each pack is trimmed, fine-tuned on the teacher labels (**knowledge distillation**), reduced to fewer layers if needed, quantized (int8 or fp16, checked against the float model), and exported to LiteRT. Neural students have two outputs: a **message head** (5 categories) and a **word head** (offensive or not, per token, joined into words).

**Efficiency methods (ablation study).** Beyond model size, the app uses: the word-list cascade (the model runs only when needed); a cache keyed by message text; only new and visible text; waiting for scrolling to settle; routing by script; short fixed input lengths (16 / 32 / 64 tokens); batching the messages of one screen; choice of CPU threads or GPU; and releasing the model when the screen is off. Each method is switched off one at a time on a fixed, recorded scrolling session on the phone, to measure its effect on model runs per minute, ms per screen, CPU time and battery.

**Evaluation.** One fixed test set per language, the same for every system:

| System | Why it is in the comparison |
|---|---|
| Word list only (v1) | What we have without a model |
| Classic character n-gram model [64] | The cheapest learned model; strong on Arabic in OSACT 2020 |
| Model2Vec (static embeddings) [65], [66] | Very fast, no word order |
| HAYAA-student [15] | Ready-made small Arabic model (message level only) |
| multilingual-toxicity-small [58] | Ready-made small multilingual model |
| Trimmed models before fine-tuning [63] | What trimming alone gives |
| **Our student (per pack)** | The contribution |
| Teachers | Upper bound (they need several GB of RAM, so they run on the laptop only) |

Metrics: macro-F1 over the 5 categories; **word-level F1** (as in the toxic-spans task [60]); false covers per 1 000 clean words; and on the Redmi 12: **real RAM, ms per message (p50/p95), CPU threads or GPU used**, battery temperature (same procedure as M4). Results with 95% confidence intervals (bootstrap over test texts). We also test whether the improvement over the word list is significant (paired bootstrap).

**Limits.** Teacher labels can be wrong or biased, especially in Arabic, which is why they are checked by humans. Public datasets come mostly from Twitter and from certain dialects. A model that is good on tweets may be weaker on other app text, so the test set also includes our own screenshots of app text.

---

## 5. Threats to validity

| Threat | Where | What we do |
|---|---|---|
| **Synthetic test data** does not match real screens | M4 | v3–v5 are evaluated on real phone screenshots (M6) |
| **One test phone** | M4, M6 | Report the phone model; where possible repeat key measurements on a second phone |
| **Heat and background load** change phone speed | M4, M6 | Pauses between runs, battery temperature recorded, airplane mode and screen brightness fixed |
| **Word lists come from one region's social media** | M5 | Manual review; test on standard-Arabic clean text |
| **Our own labels** (offensive words, people) can be biased | M5, M6 | Two annotators, Cohen's kappa, written labelling rules |
| **Keyword counting** of reviews is approximate | M3 | All low-star reviews read in full; counts reported as approximate |
| **Platform changes** (Android versions, Xiaomi system) | M1, M6 | Android version and build recorded with every result |
| **Teacher labels are wrong** (weak Arabic, cultural differences) | M7 | Several teachers, majority vote, human-checked sample with kappa |
| **Test data leaks into training** | M7 | Test set fixed first; near-duplicates removed across splits |

---

## 6. Ethics, privacy and licensing

- **Privacy by design.** Screen content is processed only in memory on the phone. The app has no internet permission and saves no screenshots (NFR-10). Screenshots collected for v5 are stored privately by the team, used only for this project, and never published. Internet pictures are used only where their license allows training.
- **Consent.** The app explains what it can see before the user turns it on (FR-1). It is a personal tool, not a monitoring tool.
- **Offensive data.** The word lists and test data contain offensive language. They are used only to build and test the filter, and are not shown in the report beyond short examples where needed.
- **Licenses.** Every source's license is recorded (§4.5, §9). AGPL-3.0 code (the competitor) was read, not copied. CC-BY-4.0 sources are credited. Attia's lexicon has no license, so the team will ask the author for permission (roadmap, Phase 0); its entries can be removed if needed (provenance column). HAYAA-student and the Mubarak list are for research use only.
- **Public user data.** Reviews and issues are reported in aggregate, without user names.
- **Models and datasets for M7.** Teacher models are open (Apache-2.0) and run offline, so no data is sent out. Cloud teachers are used only if their terms allow training on their answers. Each dataset's license is checked before use; HAYAA-student and MARBERTv2 are for research use.

**License check (2026-10-18)**, from each Hugging Face model card and GitHub repository:

| License | Models and tools | What it means for us |
|---|---|---|
| MIT / Apache-2.0 | multilingual-E5-small, Multilingual-MiniLM, mmBERT-small, multilingual-toxicity-small, potion-multilingual-128M, Zarra, CAMeLBERT-mix, DistilBERT multilingual, Qwen3Guard (8B, Stream-0.6B), Laya-multilingual, RF-DETR, PaddleOCR, LiteRT | Free to use, change and ship in the app; keep the notice |
| **AGPL-3.0** | **Ultralytics YOLO (our people model)** | Allowed, but the app that ships it must be **open source under AGPL-3.0** (our code is open anyway). A closed or paid version later would need an Ultralytics license or a switch to RF-DETR (Apache-2.0) |
| Gemma terms (gated) | Gemma 3 270M, EmbeddingGemma | Use allowed under Google's terms, with their use restrictions passed on to users |
| LFM Open License v1.0 | LFM2-350M | Free below 10 M USD yearly revenue; fine for us |
| Research use only | MARBERTv2, HAYAA-student (built on MARBERT) | Fine for experiments and comparison; **not for the shipped app** without the authors' permission |
| Not stated | AraBERTv02, ArabicBERT (asafaya) mini / medium, OSACT 2020 data, ArabicDialectSafety | Treat as research-only; ask the authors before shipping anything trained on them |
| Unreachable | GLiNER2.5-Decide (model page now redirects) | Recheck before use |

**Consequence for the design:** the shipped text model should come from the MIT / Apache group. Research-only models stay as baselines in the comparison.

---

## 7. Reproducibility

| What | Where / how |
|---|---|
| Laptop experiments | `bench/` — `source env.sh && ./run_all.sh` (details in `p0-results-linux-v1.md`, "Reproducing") |
| Phone-screen accuracy | `bench/phone.py`, `bench/phone_tflite.py` |
| Phone speed | `bench/bench_phone.py` (phone connected over adb) |
| Phone model export | `bench/export_tflite.py` |
| Combined Arabic list | `wordlists/build_ar.py` (sources in `wordlists/sources/`) |
| Own text model (v1.1) | to be added: data building, teacher labelling, training and export scripts, with fixed random seeds |
| Raw results | `bench/results/` |
| Software versions | §4.4 |
| Datasets not in the repository | COCO val2017 and annotations [7] (`bench/data/`), coco128 (Ultralytics) |

---

## 8. Use of AI tools

*This statement is final.*

The team used AI tools for two things only:

1. **Research:** searching for and summarising papers, documentation, competitor tools and user reviews. Every fact taken from a source was checked against the primary source (§4.1).
2. **Benchmark testing:** helping write and run the scripts that measure the models on our laptop and phone. Every number comes from running those scripts on our own hardware, and the outputs are kept in `bench/results/`.

AI tools were not used for anything else. The department allows AI tools (confirmed 2026-10-18). No AI tool is named as an author or co-author. The team understands, checks and is responsible for all content.

## 9. References

All online sources were accessed on **6 October 2026** unless stated otherwise.

### Papers

[1] H. Mubarak, K. Darwish, and W. Magdy, "Abusive language detection on Arabic social media," in *Proc. First Workshop on Abusive Language Online*, Vancouver, BC, Canada, Aug. 2017, pp. 52–56, doi: 10.18653/v1/W17-3008. Word list: http://alt.qcri.org/~hmubarak/offensive/ObsceneWords.txt

[2] H. Mubarak, K. Darwish, W. Magdy, T. Elsayed, and H. Al-Khalifa, "Overview of OSACT4 Arabic offensive language detection shared task," in *Proc. 4th Workshop on Open-Source Arabic Corpora and Processing Tools, with a Shared Task on Offensive Language Detection*, Marseille, France, May 2020, pp. 48–52. [Online]. Available: https://aclanthology.org/2020.osact-1.7/

[3] F. Husain, "OSACT4 shared task on offensive language detection: Intensive preprocessing-based approach," in *Proc. 4th Workshop on Open-Source Arabic Corpora and Processing Tools, with a Shared Task on Offensive Language Detection*, Marseille, France, May 2020, pp. 53–60. arXiv:2005.07297.

[4] F. Husain, "Arabic offensive language detection using machine learning and ensemble machine learning approaches," arXiv:2005.08946, 2020.

[5] I. Bensalem, M. Mout, and P. Rosso, "Offensive language detection in Arabizi," in *Proc. ArabicNLP 2023*, Singapore, Dec. 2023, pp. 423–434, doi: 10.18653/v1/2023.arabicnlp-1.36.

[6] M. Attia, "An LLM-based approach to the creation of an Arabic offensive language lexicon from annotated corpora" (arabic-offensive-words), GitHub, 2025. [Online]. Available: https://github.com/mohammedattia/arabic-offensive-words

[7] T.-Y. Lin, M. Maire, S. Belongie, L. Bourdev, R. Girshick, J. Hays, P. Perona, D. Ramanan, C. L. Zitnick, and P. Dollár, "Microsoft COCO: Common objects in context," in *Computer Vision – ECCV 2014*, 2014. arXiv:1405.0312.

[8] I. Robinson, P. Robicheaux, M. Popov, D. Ramanan, and N. Peri, "RF-DETR: Neural architecture search for real-time detection transformers," arXiv:2511.09554, 2025.

[9] N. Carion *et al.*, "SAM 3: Segment anything with concepts," arXiv:2511.16719, 2025.

### Software, models and tools

[10] Ultralytics, "Ultralytics YOLO" (YOLO11 and YOLO26 segmentation models), version 8.4.171. [Online]. Available: https://github.com/ultralytics/ultralytics

[11] Roboflow, "RF-DETR," version 1.11.1. [Online]. Available: https://github.com/roboflow/rf-detr

[12] Intel, "OpenVINO toolkit," version 2026.4.1, and "NNCF," version 3.4.0. [Online]. Available: https://github.com/openvinotoolkit/openvino, https://github.com/openvinotoolkit/nncf

[13] Google, "LiteRT" (ai-edge-litert 2.1.2) and the `benchmark_model` tool. [Online]. Available: https://ai.google.dev/edge/litert

[14] PINTO0309, "onnx2tf," version 2.6.9. [Online]. Available: https://github.com/PINTO0309/onnx2tf

[15] MahmoudMabrok, "HAYAA Student — Arabic toxicity classifier for on-device use" (HAYAA-student-int8), Hugging Face. [Online]. Available: https://huggingface.co/MahmoudMabrok/HAYAA-student-int8

[16] PaddlePaddle, "PaddleOCR: On-device deployment" (PP-OCRv5). [Online]. Available: https://www.paddleocr.ai/v3.3.1/en/version3.x/deployment/on_device_deployment.html

[17] Apache Software Foundation, "Apache Lucene: ArabicNormalizer." [Online]. Available: https://lucene.apache.org/core/8_5_1/analyzers-common/org/apache/lucene/analysis/ar/ArabicNormalizer.html

[18] R. Bor, aho-corasick (Java implementation of the Aho-Corasick algorithm), GitHub. [Online]. Available: https://github.com/robert-bor/aho-corasick

[19] "google-play-scraper" (Python package). [Online]. Available: https://pypi.org/project/google-play-scraper/

### Word lists

[20] Shutterstock / LDNOOBW, "List of dirty, naughty, obscene, and otherwise bad words," CC-BY-4.0. [Online]. Available: https://github.com/LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words

[21] LDNOOBWV2, "List of dirty, naughty, obscene and otherwise bad words, V2," CC0. [Online]. Available: https://github.com/LDNOOBWV2/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words_V2

[22] UXBERT Labs, "Arabic bad & dirty word filter list," MIT. [Online]. Available: https://github.com/uxbertlabs/arabic_bad_dirty_word_filter_list

[23] 4troDev, "profanity.csv: A multilingual profanity database," MIT. [Online]. Available: https://github.com/4troDev/profanity.csv

[24] T. Wormer, "cuss: Map of profane words to a rating of sureness" (Arabic in Latin letters), MIT. [Online]. Available: https://github.com/words/cuss

### Android, Chromium and platform documentation

[25] Android Developers, "AccessibilityService." [Online]. Available: https://developer.android.com/reference/android/accessibilityservice/AccessibilityService

[26] Android Developers, "AccessibilityNodeInfo" and API 26 differences (`EXTRA_DATA_TEXT_CHARACTER_LOCATION_KEY`). [Online]. Available: https://developer.android.com/reference/android/view/accessibility/AccessibilityNodeInfo, https://developer.android.com/sdk/api_diff/26/changes/android.view.accessibility.AccessibilityNodeInfo

[27] Android Developers, "API 34 differences: AccessibilityService" (`takeScreenshotOfWindow`, accessibility overlays). [Online]. Available: https://developer.android.com/sdk/api_diff/34/changes/android.accessibilityservice.AccessibilityService

[28] Android Open Source Project, `AccessibilityService.java` (branches android11-release, android13-release, android14-release, master) and `AbstractAccessibilityServiceConnection.java`. [Online]. Available: https://android.googlesource.com/platform/frameworks/base/+/master/core/java/android/accessibilityservice/AccessibilityService.java, https://android.googlesource.com/platform/frameworks/base/+/master/services/accessibility/java/com/android/server/accessibility/AbstractAccessibilityServiceConnection.java

[29] Android Open Source Project, "Cap alpha to max if SAW + FLAG_NOT_TOUCHABLE," commit a451d5b. [Online]. Available: https://android.googlesource.com/platform/frameworks/base/+/a451d5bae2e2

[30] Android Developers, "Tapjacking." [Online]. Available: https://developer.android.com/topic/security/risks/tapjacking

[31] Android Developers, "Media projection." [Online]. Available: https://developer.android.com/media/grow/media-projection

[32] Google, Play Console Help: policy on the use of the AccessibilityService API, answer 10964491. [Online]. Available: https://support.google.com/googleplay/android-developer/answer/10964491

[33] Google, ML Kit text recognition v2, supported languages page. [Online]. Available: https://developers.google.com/ml-kit/vision/text-recognition/v2/languages

[34] The Chromium Authors, `WebContentsAccessibilityImpl.java` (main branch). [Online]. Available: https://chromium.googlesource.com/chromium/src/+/refs/heads/main/content/public/android/java/src/org/chromium/content/browser/accessibility/WebContentsAccessibilityImpl.java

[35] Google Codelabs, "Developing an accessibility service for Android." [Online]. Available: https://codelabs.developers.google.com/codelabs/developing-android-a11y-service

[36] F. Barretta, "[Feature Request] Mali GPU support -- progress report and remaining blocker," LSFG-Android, GitHub issue #12. [Online]. Available: https://github.com/FrankBarretta/LSFG-Android/issues/12

### Competitors and related tools

[37] M. Alganzory, "HaramBlur" browser extension, source code (commit f47000e, July 2024) and issue tracker. [Online]. Available: https://github.com/alganzory/HaramBlur

[38] M. Alganzory, "HaramBlur" Android app, version 2.0.5, Google Play. [Online]. Available: https://play.google.com/store/apps/details?id=com.haramblur

[39] "SafeGaze" browser extension, Chrome Web Store. [Online]. Available: https://chrome.google.com/webstore/detail/safegaze-browser-extensio/aaddkkmpkpcnchdggomfaehpagbekalb

[40] HackaHealth Geneva, "ChiaraSelect2Speak," GPL-3.0. [Online]. Available: https://github.com/HackaHealth-Geneva/ChiaraSelect2Speak

[41] Ente, "The best open-source Android OCR." [Online]. Available: https://ente.com/blog/ocr/

### Hardware

[42] GSMArena, "Xiaomi Redmi 12 — Full phone specifications," and Xiaomi, "Redmi 12 specs." [Online]. Available: https://m.gsmarena.com/xiaomi_redmi_12-ampp-12328.php, https://www.mi.com/global/redmi-12/specs

### Linux phase (plan B, paused)

[43] micha4w, "Hypr-DarkWindow." [Online]. Available: https://github.com/micha4w/Hypr-DarkWindow

[44] the-bmt, "HyprWindowShade." [Online]. Available: https://github.com/the-bmt/HyprWindowShade

[45] hyprwm, Hyprland pull request #13272 (Vulkan renderer, work in progress), GitHub. [Online]. Available: https://github.com/hyprwm/Hyprland/pull/13272

[46] DeepWiki, Hyprland: rendering pipeline (section 6.1). [Online]. Available: https://deepwiki.com/hyprwm/Hyprland/6.1-rendering-pipeline

[47] LattePanda, blog post on YOLO11 with OpenVINO on the LattePanda Mu (integrated GPU). [Online]. Available: https://www.lattepanda.com/blog-323240.html

[48] Roboflow, blog post on RF-DETR segmentation checkpoints. [Online]. Available: https://blog.roboflow.com/rf-detr-segmentation/

### Text model (v1.1)

[49] TypeSafe AI, "Jev" decision model (Jev 1.13, released Sep. 2026). [Online]. Available: https://openrouter.ai/typesafe/jev-1.13/api; overview: https://startuphub.ai/ai-news/artificial-intelligence/2026/typesafe-jev-model-kills-chat

[50] DataCamp, overview of open-source alternatives to TypeSafe Jev (Laya, Von, Kev, NanoJev, and others). [Online]. Available: https://www.datacamp.com/blog/top-open-source-jev-alternatives

[51] ConvAI Innovations, "Laya" and "Laya-multilingual," Apache-2.0, Hugging Face. [Online]. Available: https://huggingface.co/convaiinnovations/laya-multilingual

[52] LiteRT Community, "Laya-Multilingual-LiteRT" (phone build with measured latency), Hugging Face. [Online]. Available: https://huggingface.co/litert-community/Laya-Multilingual-LiteRT

[53] Fastino, "GLiNER2.5-Decide," Apache-2.0, Hugging Face. [Online]. Available: https://huggingface.co/fastino/gliner2.5-decide

[54] H. Zhao *et al.*, "Qwen3Guard technical report," arXiv:2510.14276, 2025.

[55] M. Marone, O. Weller, W. Fleshman, E. Yang *et al.*, "mmBERT: A modern multilingual encoder with annealed language learning," arXiv:2509.06888, 2025.

[56] W. Zaghouani, M. R. Biswas, K. K. Aldous, and M. Bessghaier, "ArabicDialectSafety: A dialect-aware benchmark for Arabic content safety classification," arXiv:2608.01291, 2026.

[57] F. Alam, M. R. Biswas, M. B. Kmainasi, A. E. Shahroor *et al.*, "ArGuard shared task: Harmful content detection in Arabic memes and LLM prompts," arXiv:2609.29349, 2026.

[58] Horizon Labs, "multilingual-toxicity-small" (mmBERT-small), Apache-2.0, Hugging Face. [Online]. Available: https://huggingface.co/Horizon-Labs/multilingual-toxicity-small

[59] M. Fatehkia, E. Altinisik, and H. T. Sencar, "FanarGuard: A culturally-aware moderation filter for Arabic language models," arXiv:2511.18852, 2025.

[60] J. Pavlopoulos, J. Sorensen, L. Laugier, and I. Androutsopoulos, "SemEval-2021 Task 5: Toxic spans detection," in *Proc. 15th Int. Workshop on Semantic Evaluation (SemEval-2021)*, 2021, pp. 59–69, doi: 10.18653/v1/2021.semeval-1.6.

[61] M. Abdul-Mageed, A. Elmadany, and E. M. B. Nagoudi, "ARBERT & MARBERT: Deep bidirectional transformers for Arabic," in *Proc. 59th Annual Meeting of the ACL and 11th IJCNLP (Volume 1: Long Papers)*, 2021, doi: 10.18653/v1/2021.acl-long.551.

[62] G. Inoue, B. Alhafni, N. Baimukan, H. Bouamor, and N. Habash, "The interplay of variant, size, and task type in Arabic pre-trained language models," in *Proc. Sixth Arabic Natural Language Processing Workshop*, 2021. [Online]. Available: https://aclanthology.org/2021.wanlp-1.10/

[63] A. Ushio, Y. Zhou, and J. Camacho-Collados, "Efficient multilingual language model compression through vocabulary trimming," in *Findings of the Association for Computational Linguistics: EMNLP 2023*, 2023, pp. 14725–14739, doi: 10.18653/v1/2023.findings-emnlp.981.

[64] S. Hassan, Y. Samih, H. Mubarak, A. Abdelali, A. Rashed, and S. A. Chowdhury, "ALT submission for OSACT shared task on offensive language detection," in *Proc. 4th Workshop on Open-Source Arabic Corpora and Processing Tools, with a Shared Task on Offensive Language Detection*, Marseille, France, May 2020, pp. 61–65. [Online]. Available: https://aclanthology.org/2020.osact-1.9/

[65] MinishLab, "Model2Vec: Fast state-of-the-art static embeddings." [Online]. Available: https://github.com/MinishLab/model2vec

[66] MinishLab, "potion-multilingual-128M," MIT, and NAMAA-Space, "Zarra" (Arabic Model2Vec model), MIT, Hugging Face. [Online]. Available: https://huggingface.co/minishlab/potion-multilingual-128M, https://huggingface.co/NAMAA-Space/zarra

[67] H. Schechter Vera, S. Dua, B. Zhang, D. Salz, R. Mullins *et al.*, "EmbeddingGemma: Powerful and lightweight text representations," arXiv:2509.20354, 2025.

[68] Google, "Introducing Gemma 3 270M: The compact model for hyper-efficient AI," Google Developers Blog. [Online]. Available: https://developers.googleblog.com/introducing-gemma-3-270m/

[69] L. Wang, N. Yang, X. Huang, L. Yang, R. Majumder *et al.*, "Multilingual E5 text embeddings: A technical report," arXiv:2402.05672, 2024.

[70] Google, "Streamlining LLM inference at the edge with TFLite," Google Developers Blog. [Online]. Available: https://developers.googleblog.com/en/streamlining-llm-inference-at-the-edge-with-tflite/


*References [71]–[95] were added for the related-work review in [`research-en.html`](research-en.html) (accessed 18 October 2026).*

[71] T. Davidson, D. Warmsley, M. Macy, and I. Weber, "Automated hate speech detection and the problem of offensive language," in *Proc. ICWSM*, 2017, pp. 512–515.

[72] A. Schmidt and M. Wiegand, "A survey on hate speech detection using natural language processing," in *Proc. Fifth Int. Workshop on Natural Language Processing for Social Media*, Valencia, Spain, 2017, pp. 1–10, doi: 10.18653/v1/W17-1101.

[73] M. Zampieri, S. Malmasi, P. Nakov, S. Rosenthal, N. Farra, and R. Kumar, "SemEval-2019 Task 6: Identifying and categorizing offensive language in social media (OffensEval)," in *Proc. SemEval-2019*, 2019, pp. 75–86, doi: 10.18653/v1/S19-2010.

[74] M. Zampieri *et al.*, "SemEval-2020 Task 12: Multilingual offensive language identification in social media (OffensEval 2020)," in *Proc. Fourteenth Workshop on Semantic Evaluation*, 2020, pp. 1425–1447, doi: 10.18653/v1/2020.semeval-1.188.

[75] H. Mubarak, H. Al-Khalifa, and A. Al-Thubaity, "Overview of OSACT5 shared task on Arabic offensive language and hate speech detection," in *Proc. 5th Workshop on Open-Source Arabic Corpora and Processing Tools*, Marseille, France, 2022, pp. 162–166. [Online]. Available: https://aclanthology.org/2022.osact-1.20

[76] I. Bensalem, P. Rosso, and H. Zitouni, "Toxic language detection: A systematic review of Arabic datasets," arXiv:2312.07228, 2024.

[77] G. Hinton, O. Vinyals, and J. Dean, "Distilling the knowledge in a neural network," arXiv:1503.02531, 2015.

[78] V. Sanh, L. Debut, J. Chaumond, and T. Wolf, "DistilBERT, a distilled version of BERT: Smaller, faster, cheaper and lighter," arXiv:1910.01108, 2019.

[79] F. Gilardi, M. Alizadeh, and M. Kubli, "ChatGPT outperforms crowd workers for text-annotation tasks," *Proc. Natl. Acad. Sci. USA*, vol. 120, no. 30, e2305016120, 2023, doi: 10.1073/pnas.2305016120.

[80] Y. Du *et al.*, "PP-OCR: A practical ultra lightweight OCR system," arXiv:2009.09941, 2020.

[81] C. Cui *et al.*, "PaddleOCR 3.0 technical report," arXiv:2507.05595, 2025.

[82] J. Redmon, S. Divvala, R. Girshick, and A. Farhadi, "You only look once: Unified, real-time object detection," in *Proc. IEEE CVPR*, 2016, pp. 779–788.

[83] K. He, G. Gkioxari, P. Dollár, and R. Girshick, "Mask R-CNN," in *Proc. IEEE ICCV*, 2017, doi: 10.1109/ICCV.2017.322.

[84] D. Bolya, C. Zhou, F. Xiao, and Y. J. Lee, "YOLACT: Real-time instance segmentation," in *Proc. IEEE/CVF ICCV*, 2019, pp. 9157–9166.

[85] F. C. Akyon, S. O. Altinuc, and A. Temizel, "Slicing aided hyper inference and fine-tuning for small object detection," in *Proc. IEEE ICIP*, Bordeaux, France, 2022, pp. 966–970, doi: 10.1109/ICIP46576.2022.9897990.

[86] B. Jacob *et al.*, "Quantization and training of neural networks for efficient integer-arithmetic-only inference," in *Proc. IEEE/CVF CVPR*, 2018, pp. 2704–2713.

[87] A. Ignatov *et al.*, "AI Benchmark: All about deep learning on smartphones in 2019," in *Proc. IEEE/CVF ICCV Workshops*, 2019, pp. 3617–3635, doi: 10.1109/ICCVW.2019.00447.

[88] M. Moustafa, "Applying deep learning to classify pornographic images and videos," arXiv:1511.08899, 2015.

[89] R. McPherson, R. Shokri, and V. Shmatikov, "Defeating image obfuscation with deep learning," arXiv:1609.00408, 2016.

[90] M. C. Potter, B. Wyble, C. E. Hagmann, and E. S. McCourt, "Detecting meaning in RSVP at 13 ms per picture," *Atten. Percept. Psychophys.*, vol. 76, no. 2, pp. 270–279, 2014, doi: 10.3758/s13414-013-0605-z.

[91] Y. Fratantonio, C. Qian, S. P. Chung, and W. Lee, "Cloak and dagger: From two permissions to complete control of the UI feedback loop," in *Proc. IEEE Symp. Security and Privacy*, 2017, pp. 1041–1057, doi: 10.1109/SP.2017.39.

[92] Apple, "About Communication Safety on your child's Apple device," Apple Support, article 105069. [Online]. Available: https://support.apple.com/en-us/105069

[93] Google, "Sensitive content warnings in Google Messages," Google Messages Help, answer 15724426. [Online]. Available: https://support.google.com/messages/answer/15724426

[94] A. V. Aho and M. J. Corasick, "Efficient string matching: An aid to bibliographic search," *Commun. ACM*, vol. 18, no. 6, pp. 333–340, 1975, doi: 10.1145/360825.360855.

[95] J. Cohen, "A coefficient of agreement for nominal scales," *Educ. Psychol. Meas.*, vol. 20, no. 1, pp. 37–46, 1960, doi: 10.1177/001316446002000104.

[96] Google, "MediaPipe Image Segmenter: models," Google AI Edge. [Online]. Available: https://developers.google.com/edge/mediapipe/solutions/vision/image_segmenter

[97] C. Zhang *et al.*, "Faster Segment Anything: Towards lightweight SAM for mobile applications," arXiv:2306.14289, 2023.

[98] C. Zhou, X. Li, C. C. Loy, and B. Dai, "EdgeSAM: Prompt-in-the-loop distillation for on-device deployment of SAM," arXiv:2312.06660, 2023.

[99] X. Zhao *et al.*, "Fast Segment Anything," arXiv:2306.12156, 2023.
