# HaramBlurr — Roadmap

Date: 2026-10-06 · Start of plan: **Week 1 = Mon 12 Oct 2026** · Team: 3 students
Details of each step: [`investigation-android-v1.md`](investigation-android-v1.md) §10. Requirements: SRS v2.1 (`srs-en.html`). Methods: [`research-methods.md`](research-methods.md).

> **The submission deadline is not known yet.** The weeks below are estimates of effort. When the deadline is fixed, move the "Report and defense" block to the end and shorten the optional items first.

---

## 1. Overview

```
Wk  1   2   3   4   5   6   7   8   9  10  11  12  13  14  15  16  17  18  19  20  21  22
    ├─ v1: bad-language text ─┤
    [0][v1-a ][v1-b    ][eval]
    [ v1-c word lists ]
        ├──────── v1.1: own text model (teachers → data → student → phone) ───┤
                                    ├─ v2: big people ──┤├ v3: med. ┤
                                                                    ├──── v4: small people ────┤
    [ report written continuously ..................................................] [report+def.]
```

| Phase | Weeks | Hides | Exit criterion (must be true to move on) |
|---|---|---|---|
| **0. Housekeeping** | 1 | — | Git repo; phone speed test (P0b) finished; Android version of the test phone known; email sent to Attia |
| **v1. Bad-language text** | 1–5 | Arabic + English bad words | NFR-1 (≥ 95% of listed words hidden), NFR-2 (≤ 1 false cover / 1 000 clean words), NFR-3 (gap ≤ 3 frames) measured and reported |
| **v1.1. Own text model** | 2–9 (parallel) | Context-dependent words, insults without bad words | Per language pack, NFR-13 on the Redmi 12: real RAM ≤ 100 MB, ≤ 50 ms per message (p95), about one CPU core at most; and better than the word list and the cheaper baselines on the same test set |
| **v2. Big people** | 8–11 | People > ~96 px | ≥ 95% of big people hidden on real phone screenshots; waiting time ≤ 0.7 s |
| **v3. Medium people** | 12–13 | People ~32–96 px | ≥ 95% of medium people hidden; check speed fits (tiles) |
| **v4. Small people** | 14–19 | People < ~32 px | Our trained model beats the base model on small people (target 95%) |
| **Report and defense** | 20–22 | — | Final report, demo video, slides |

**Done before Week 1:** research, the people-model tests on laptop and phone (P0), the HaramBlur study, the combined Arabic word list, SRS v2.1, proposal.

---

## 2. Workstreams

Three people, three streams. The team decides who takes which.

| Stream | Owns | Main output |
|---|---|---|
| **A. Android app** | Accessibility service, covers, settings, notification, scroll tracking; later the window picture and model in the app | The APK |
| **B. Language and data** | Arabic and English word lists, categories, test sets, measuring v1; later the phone-screenshot dataset for v4 | `wordlists/`, test results |
| **C. AI models** | Phone speed tests; **our own text model (v1.1)**: teachers, training, phone export; people detection, tiles, training for v4; text-in-images (PaddleOCR) if time allows | Model files, results docs |

Everyone writes their own part of the report as they go (§5).

---

## 3. Phase by phase

### Phase 0 — Housekeeping (Week 1)

| Task | Stream | Size |
|---|---|---|
| Put the project in **git** (code, docs, word lists; not `.venv`, datasets or model files) | all | 1 h |
| Finish the phone speed test: `bench/bench_phone.py` (fp32 / fp16 / drq, CPU / GPU / NNAPI, 640 and 480 px) | C | 1 evening |
| Check the Redmi 12's Android version (13 or 14 decides the v2 method) | A | 5 min |
| Email Mohammed Attia: permission to use his lexicon | B | 15 min |
| Ask the department: deadline, report format, supervisor | all | — |

### v1 — Bad-language text (Weeks 1–5)

| Step | Weeks | Stream | What | Done when |
|---|---|---|---|---|
| v1-a App skeleton | 1–2 | A | Accessibility service, overlay, settings, notification, consent screen (FR-1, FR-2, FR-4). Log the text it reads. Start from the Google codelab. | A list of which popular apps share their text |
| v1-b Text filter | 2–4 | A | Cleaning, matching, word boxes, cover word / message, covers follow scrolling, language choice with packs and routing by script (FR-3, FR-5 to FR-9, FR-11, FR-21) | Works in Chrome, WhatsApp, Facebook, X, YouTube comments |
| v1-c Word lists | 1–4 | B | Review `wordlists/ar_combined.tsv`: keep standard Arabic, sort into 4 categories, write blasphemy phrases, move normal words to "phrase only". Review the English list. | Final list with a category for every entry |
| v1 evaluation | 5 | B + A | Measure NFR-1, NFR-2, NFR-3 and battery (method: research-methods §4.6) | Numbers in a results doc |

**Decision after v1-b:** if the gap before the cover is more than 3 frames, cover a bit more text around changes, and write it up honestly as a limit of Android.

### v1.1 — Our own text model (Weeks 2–9, in parallel with v1)

Design: investigation §3.5. Method: research-methods §4.7.

| Weeks | Stream | What | Done when |
|---|---|---|---|
| 2 | C | **P0c step 1 (phone test)**: export all candidates (investigation §3.5), trimmed to one language, to LiteRT; on the Redmi 12 measure real RAM, ms per message at 16 / 32 / 64 tokens, CPU 1/2/4 threads and GPU | A table; only candidates meeting NFR-13 go on |
| 2–3 | C | Set up the teachers on the laptop or Colab (Qwen3Guard-8B, Laya). Write the typed questions (offensive? category? which words?). Check the terms of any API teacher. | Teachers answer on a small Arabic sample |
| 3–5 | B + C | Build the data: OSACT 2020, Mubarak 2017, ArabicDialectSafety (standard Arabic), list-matched sentences, clean text. Teacher labels by majority vote. | Labelled train / dev / test sets |
| 5 | B | Check a sample of teacher labels by hand (two people), Cohen's kappa | Agreement reported; bad labels fixed |
| 5 | C | **P0c step 2 (quality test)**: quick fine-tune of the remaining candidates on a small dev set per language | One model chosen per language pack |
| 5–7 | C | Train each pack's student: trimmed, distilled from the teachers, fewer layers if needed, two heads (message category, word-level), int8 / fp16. Add the efficiency methods (cache, batching, short inputs). | Meets NFR-13 in a phone benchmark |
| 7–8 | C + A | Measure on the Redmi 12; put it in the app as layer ② | Runs inside the app |
| 8–9 | B + C | Compare per language on the same test set: word list · classic n-gram model · Model2Vec · HAYAA-student · multilingual-toxicity-small · our model · teachers; plus the efficiency ablation on a recorded scrolling session | Results tables (thesis chapter 7) |

**Interim:** if v1 needs the second layer before our model is ready, use HAYAA-student (research license) as a stand-in.

### v2 — Big people (Weeks 8–11)

| Step | Stream | What |
|---|---|---|
| Window picture + hide first | A | `takeScreenshotOfWindow` (Android 14+), cover on change, uncover after check (FR-14) |
| Model in the app | C | LiteRT + NMS, the fastest config from P0b, mask cover (FR-13) |
| Test set | B | Real phone screenshots (feeds, video apps), people labelled by size |
| Evaluation | B + C | NFR-4 (big), NFR-5, NFR-6, battery |

**Decision before v2 (from P0b):** if no model setup checks a full screen in ≤ 150 ms, tiles will not fit on this phone. Then v3 needs a smaller input size, a faster phone, or fewer tiles, and the plan is adjusted.

### v3 — Medium people (Weeks 12–13)

Tiles (FR-17) using the fastest setup, with tiles checked only where the screen changed. Measure medium-people recall against speed.

### v4 — Small people (Weeks 14–19)

| Weeks | Stream | What |
|---|---|---|
| 14–15 | B | Collect phone screenshots (feeds, grids, video apps, games). Store them safely and privately. |
| 15–16 | C | Label people with SAM 3 (text prompt "person"), and check a sample by hand |
| 16–18 | C | Fine-tune the people model on these screenshots, then export it to the phone again |
| 19 | B + C | Evaluate on a held-out set: small / medium / large recall, false covers |

### Report and defense (Weeks 20–22)

Final report, demo video (record the screen with the filter on), slides, practice defense.

---

## 4. Later, if time allows

| Item | Why later |
|---|---|
| Text inside images and videos (PaddleOCR, Arabic) | Separate pipeline; the team has PaddleOCR experience, so it is the first optional item |
| Arabic dialects and Arabizi | The word list already has 959 Arabizi entries; needs review |
| Android 13 fallback (FR-16) | Only if the test phone or users need it |
| Video mode (FR-19) | Needs more checks per second than the phone gives today |

---

## 5. Report plan (written while working, not at the end)

| Chapter | Written in | From |
|---|---|---|
| 1. Introduction, problem, goals | Week 1 | Proposal, SRS §1 |
| 2. Background and related work | Weeks 1–3 | Investigation §2, §9; research-methods §4.1–§4.3 |
| 3. Requirements | Week 2 | SRS v2.1 |
| 4. Research methods | Week 2, updated each phase | [`research-methods.md`](research-methods.md) |
| 5. Design | Weeks 2–9 | Investigation §3–§5 |
| 6. Implementation | Each phase | Code and phase notes |
| 7. Evaluation and results | Each phase | Results docs (P0, v1, v1.1 model comparison, v2, v3, v4) |
| 8. Discussion, limits, future work | Weeks 20–21 | All of the above |
| References | Continuously | research-methods §9 |

---

## 6. Key risks to the schedule

| Risk | When we know | Plan B |
|---|---|---|
| Phone too slow for people detection | End of Week 1 (P0b) | Smaller input, fewer tiles, or a stronger test phone |
| Test phone is Android 13 | Week 1 | Update it, borrow an Android 14+ phone, or use the screen-capture fallback |
| Arabic list review takes longer than planned | Week 3 | Ship v1 with swearing and sexual first; insults and blasphemy next |
| Attia says no | Any time | Remove the 239 entries that only come from his lexicon |
| Teachers are weak in Arabic (low agreement with our labels) | Week 5 | Use more human labels on a smaller set; use the Arabic-specific base model (CAMeLBERT) |
| Our text model is too slow or uses too much RAM on the phone (NFR-13) | Week 2 (P0c), confirmed Week 7 | Fewer layers, smaller vocabulary, shorter inputs, run it only on context-dependent messages |
| v4 data or training takes too long | Week 17 | Report v4 as partial results; v1–v3 are complete products on their own |
