# Roadmap

Date: 2026-10-18 (re-planned; first version 2026-10-06) · Start of plan: **Week 1 = Mon 12 Oct 2026** · Team: 3 students
Details of each step: [`investigation-android-v1.md`](investigation-android-v1.md) §10. Requirements: SRS v2.2 (`srs-en.html`). Methods: [`research-methods.md`](research-methods.md).

> **Deadline: about six months from 18 Oct 2026, so around mid-April 2027 (Week 27).** The exact date is not fixed yet. If it moves, keep "Report and defense" at the end and shorten v5 (bonus) first.

> **Graduation scope (agreed 2026-10-18):** **v1 to v4 are the graduation project** (text with a word list and our own text model, text in images, big and medium people). **v5 (small people) is a bonus**: started only when v4 meets its exit criterion, and reported as far as it got. **v6 (video) is after graduation**: it goes in the report as future work only.

---

## 1. Overview

```
Wk  1   2   3   4   5   6   7   8   9   10  11  12  13  14  15  16  17  18  19  20  21  22  23  24  25  26  27
    ├──── v1 text: word list + our own text model ────┤
                    ├P0d┤
                        ├v2 text in images┤
                                        ├─ v3 big ┤
                                                    ├─v4 med─┤
                                                                ├─ test v1–v4 ─┤
                                                                    ├╌╌╌╌ v5 small people (bonus) ╌╌╌╌┤
                                                                                            ├─── report+defense ───┤
    [ report written continuously ..........................................................]
```

| Phase | Weeks | Hides | Exit criterion (must be true to move on) |
|---|---|---|---|
| **0. Housekeeping** | 1–2 | — | Git repo ✅; phone speed test (P0b) ✅; Android version of the test phone ✅; email sent to Attia; streams assigned |
| **v1. Bad-language text** (word list + our own model) | 1–9 | Arabic + English bad words, context-dependent words, insults without bad words | Word list: NFR-1 (≥ 95% of listed words hidden), NFR-2 (≤ 1 false cover / 1 000 clean words), NFR-3 (gap ≤ 3 frames). Model, per language pack, NFR-13 on the Redmi 12: real RAM ≤ 100 MB, ≤ 50 ms per message (p95), about one CPU core at most; and better than the word list and the cheaper baselines on the same test set |
| **v2. Text inside images** | 5 (P0d), 6–9 | Bad words in memes, thumbnails, subtitles burned into videos | OCR phone test done (P0d); NFR-14 targets set from it and measured on real screenshots |
| **v3. Big people** | 10–12 | People > ~96 px | ≥ 95% of big people hidden on real phone screenshots; waiting time ≤ 0.7 s |
| **v4. Medium people** | 13–15 | People ~32–96 px | ≥ 95% of medium people hidden; check speed fits (tiles) |
| **Test v1–v4 together** | 16–18 | — | Full evaluation on real screenshots, battery over a day, fixes; **this is the graduation product** |
| *v5. Small people (bonus)* | *17–22* | *People < ~32 px* | *Only if v4 passed. Our trained model beats the base model on small people (target 95%)* |
| ~~v6. Video~~ | after graduation | People in videos while they play | Future work chapter only |
| **Report and defense** | 22–27 | — | Final report, demo video, slides |

**Done before Week 1:** research, the people-model tests on laptop and phone (P0, P0b), the study of the competing HaramBlur app, the combined Arabic word list, SRS, proposal.

**Rules agreed on 2026-10-18:** Android 14+ only for now (no fallback for older phones). Apps that block screenshots (banking, some video apps) are not checked. AI tools may be used for the project.

---

## 2. Workstreams

Three people, three streams. The team decides who takes which.

| Stream | Owns | Main output |
|---|---|---|
| **A. Android app** | Accessibility service, covers, settings, notification, scroll tracking; from v2 the window picture and the models in the app | The APK |
| **B. Language and data** | Arabic and English word lists, categories, test sets, measuring v1; screenshot test sets for v2; the people dataset for v5 | `wordlists/`, test results |
| **C. AI models** | Phone speed tests; **our own text model (v1)**; Arabic OCR (PaddleOCR) for v2; people detection, tiles, training for v5 (bonus) | Model files, results docs |

Everyone writes their own part of the report as they go (§5).

---

## 3. Phase by phase

### Phase 0 — Housekeeping (Weeks 1–2)

| Task | Stream | Status |
|---|---|---|
| Put the project in **git** | all | ✅ 2026-10-07 |
| Finish the phone speed test (P0b) | C | ✅ 2026-10-07 (GPU ~205 ms at 640 px) |
| Check the Redmi 12's Android version | A | ✅ Android 15 |
| Google Play developer account | all | ✅ Already exists (the team published another app on 2026-10-07) |
| Ask the department: deadline, AI-tool rules | all | ✅ About six months; AI tools allowed |
| Email Mohammed Attia: permission to use his lexicon | B | Open |
| Assign the three streams | all | Open |

### v1 — Bad-language text (Weeks 1–9)

v1 has two layers built together: the **word list** (part 1) and **our own small text model** (part 2). Until 2026-10-18 the model was a separate version, "v1.1"; older documents still use that name for it.

#### v1 part 1 — App and word list (Weeks 1–5)

| Step | Weeks | Stream | What | Done when |
|---|---|---|---|---|
| v1-a App skeleton | 1–2 | A | Accessibility service, overlay, settings, notification, consent screen (FR-1, FR-2, FR-4). Log the text it reads. Start from the Google codelab. | A list of which popular apps share their text |
| v1-b Text filter | 2–4 | A | Cleaning, matching, word boxes, cover word / message, covers follow scrolling, language choice with packs and routing by script (FR-3, FR-5 to FR-9, FR-11, FR-21) | Works in Chrome, WhatsApp, Facebook, X, YouTube comments |
| v1-c Word lists | 1–4 | B | Review `wordlists/ar_combined.tsv`: keep standard Arabic, sort into 4 categories, write blasphemy phrases, move normal words to "phrase only". Review the English list. | Final list with a category for every entry |
| v1 evaluation | 5 | B + A | Measure NFR-1, NFR-2, NFR-3 and battery (method: research-methods §4.6) | Numbers in a results doc |

**Decision after v1-b:** if the gap before the cover is more than 3 frames, cover a bit more text around changes, and write it up honestly as a limit of Android.

#### v1 part 2 — Our own text model (Weeks 2–9, in parallel with part 1)

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

**Interim:** if part 1 needs the second layer before our model is ready, use HAYAA-student (research license) as a stand-in.

### v2 — Text inside images (Week 5 test, Weeks 6–9)

v2 builds the **window picture** step (`takeScreenshotOfWindow`, Android 14+) that the people versions reuse.

| Weeks | Stream | What | Done when |
|---|---|---|---|
| 5 | C | **P0d (OCR phone test)**: PaddleOCR PP-OCRv5 Arabic and English mobile models on the Redmi 12: ms per screen, RAM, CPU vs GPU; accuracy on a small set of meme and thumbnail screenshots | A table; NFR-14 targets set |
| 6–7 | A | Window picture on screen change (max 3 per second), find image areas, hide first over changed images (FR-14) | Pictures arrive in the app, nothing saved to disk |
| 6–8 | C + A | OCR in the app; the read text goes through the same filter as v1 (word list and model); cover the word boxes inside the image (FR-12) | Bad words inside images are covered |
| 8–9 | B | Test set: real screenshots with text in images (memes, thumbnails, video subtitles); measure NFR-14 and the waiting time | Numbers in a results doc |

### v3 — Big people (Weeks 10–12)

| Step | Stream | What |
|---|---|---|
| Model in the app | C | LiteRT + NMS on the GPU at 640 px (fastest setup from P0b), mask cover (FR-13) |
| Hide first | A | Reuse the v2 window picture: cover on change, uncover after check (FR-14) |
| Test set | B | Real phone screenshots (feeds, video apps), people labelled by size |
| Evaluation | B + C | NFR-4 (big), NFR-5, NFR-6, battery |

**Known from P0b:** no setup checks a full screen in ≤ 150 ms at 640 px (GPU ~205 ms), so tiles cannot run on every change. v4 checks tiles only where the screen changed.

### v4 — Medium people (Weeks 13–15)

Tiles (FR-17) on the GPU, checked only where the screen changed. Measure medium-people recall against speed.

### Test v1–v4 together (Weeks 16–18)

All four versions running at once on the Redmi 12: NFR-1 to NFR-7 and NFR-13/14 on real screenshots, battery over a normal day, crash and stop handling. Fix what breaks. The result is the product we defend.

### v5 — Small people (bonus, Weeks 17–22)

**Bonus, not promised.** Starts only when v4 has met its exit criterion. Data collection (Stream B) may start earlier because it does not touch the app. If it is not finished, the report shows the partial results.

| Weeks | Stream | What |
|---|---|---|
| 17–18 | B | Collect data: the team's own phone screenshots (feeds, grids, video apps, games), kept private and never published, plus openly licensed pictures from the internet |
| 18–19 | C | Label people with SAM 3 (text prompt "person"), and check a sample by hand |
| 19–21 | C | Fine-tune the people model on this data (optionally with RF-DETR as a teacher), then export it to the phone again. Same size and speed as today. |
| 22 | B + C | Evaluate on a held-out set: small / medium / large recall, false covers |

### v6 — Video (after graduation)

**Not part of the graduation project.** The report names it as future work. The window picture gives at most 3 pictures per second, which cannot follow a playing video. Options for later:

| Option | Idea |
|---|---|
| Tracking | Check every ~333 ms and move the covers with the people between checks |
| Faster source for video only | Screen capture while a video plays, if the permission prompt is acceptable |
| Strict mode | Keep the video area covered while it plays; uncover when paused and checked |

### Report and defense (Weeks 22–27)

Final report, demo video (record the screen with the filter on), slides, practice defense.

---

## 4. Later, if time allows

| Item | Why later |
|---|---|
| Arabic dialects and Arabizi | The word list already has 959 Arabizi entries; needs review |
| A short product name | Candidate: **Sitr (سِتر)**. Check the Play Store for clashes first (issue #4) |
| Android 13 and older (FR-16) | Dropped for now: the app is built for Android 14+ first |
| Pictures of apps that block screenshots (banking, Netflix and other protected video apps) | Android does not allow it; their screen text is still filtered. Named as a limit in the report |

---

## 5. Report plan (written while working, not at the end)

| Chapter | Written in | From |
|---|---|---|
| 1. Introduction, problem, goals | Week 1 | Proposal, SRS §1 |
| 2. Background and related work | Weeks 1–3 | Investigation §2, §9; research-methods §4.1–§4.3 |
| 3. Requirements | Week 2 | SRS v2.2 |
| 4. Research methods | Week 2, updated each phase | [`research-methods.md`](research-methods.md) |
| 5. Design | Weeks 2–12 | Investigation §3–§5, app design |
| 6. Implementation | Each phase | Code and phase notes |
| 7. Evaluation and results | Each phase | Results docs (P0, v1 including the text-model comparison, v2 to v4, v5 if done) |
| 8. Discussion, limits, future work | Weeks 22–25 | All of the above; v6 (video) and, if not done, v5 as future work |
| References | Continuously | research-methods §9 |

---

## 6. Key risks to the schedule

| Risk | When we know | Plan B |
|---|---|---|
| Arabic list review takes longer than planned | Week 3 | Ship v1 with swearing and sexual first; insults and blasphemy next |
| Attia says no | Any time | Remove the 239 entries that only come from his lexicon |
| Teachers are weak in Arabic (low agreement with our labels) | Week 5 | Use more human labels on a smaller set; use the Arabic-specific base model (CAMeLBERT) |
| Our text model is too slow or uses too much RAM on the phone (NFR-13) | Week 2 (P0c), confirmed Week 7 | Fewer layers, smaller vocabulary, shorter inputs, run it only on context-dependent messages |
| Arabic OCR too slow or weak on the phone | Week 5 (P0d) | Check only images that changed, smaller input, English first |
| v4 late, so no time for v5 | Week 15 | Skip v5 (it is a bonus); v1–v4 are the graduation product |
| v5 data or training takes too long | Week 21 | Report v5 as partial results |
