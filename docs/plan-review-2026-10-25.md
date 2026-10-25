# Plan Review (before v1-a)

Date: 2026-10-25 (end of Week 2) · Status: **review, for team decision** · Reviewed: [`roadmap.md`](roadmap.md), [`app-design-v1.md`](app-design-v1.md), SRS v3.0 (`srs-en.html`), [`investigation-android-v1.md`](investigation-android-v1.md), [`p0-results-android-v1.md`](p0-results-android-v1.md), [`issue.md`](issue.md), [`asbuild.md`](asbuild.md), [`research-methods.md`](research-methods.md), [`../wordlists/`](../wordlists/README.md).

**Verdict.** The plan is well evidenced: the platform choice is backed by AOSP source, the people model by real phone numbers, and every decision is logged. The architecture (one accessibility service + one trusted overlay + the window picture) is the right one for a non-rooted phone. Four points need a decision **before v1-a starts** (§1). The rest are gaps to fix in the design document rather than in code later (§2, §3). §4 lists the concrete changes proposed, each with a suggested owner.

---

## 1. The four points that matter most

### 1.1 NFR-3 (text cover within 3 frames) cannot be met on Android

- **Why.** The accessibility event is dispatched *after* the app has drawn. The service then does several IPC round trips (root window, node traversal, `refreshWithExtraData` for the per-letter boxes), posts to the overlay, and waits for a vsync. Expect roughly **100–300 ms** end to end, not 33 ms.
- **The roadmap's fallback does not help.** "Cover a bit more text around changes" does not shorten the gap; the text has already been seen.
- **Proposal.** Re-baseline NFR-3 to a measured target (for example **≤ 100 ms p95**, Nielsen's "instant" limit), state plainly in the SRS and the report that plain text is *not* hide-first (SRS §2.3 already argues this), and measure the gap in the **first week of v1-b**, before it is written anywhere else.

### 1.2 Autoplay video breaks the v3 promise on the main target apps, and it is deferred to after graduation

- **Why.** Instagram, TikTok, X and YouTube Shorts are feeds of *playing* video. Video frames in a `SurfaceView` / `TextureView` generate **no accessibility events**: the view tree does not change. An event-driven service sees nothing change and never re-checks. People in a playing video stay uncovered between checks, and no event wakes the service. This is not the v6 problem (following movement at 3 pictures per second). It is a **v3 problem**: knowing that content changed at all. It also breaks NFR-8's "no work while the screen is still" as a definition of "still".
- **Proposal.** Design a video policy in v3, in one of two cheap forms, and measure the battery cost of each:
  1. **Strict**: detect video nodes (class name of a player / surface view, or a large image area that changes between two pictures) and keep them covered while they play; uncover when paused and checked.
  2. **Poll**: while a video node is on screen, take window pictures at the 333 ms limit and re-check, independent of events.
  Both give a partial v6 for free; v6 proper (tracking between checks) stays future work.

### 1.3 Stream C is over-committed, and the text model has two unbudgeted hard parts

- **Load.** Weeks 2–9 ask one person to export ~15 candidates to LiteRT, set up teachers, label data, train two-headed students for two languages, quantize, integrate, *and* run the OCR phone test (P0d) in Week 5, *and* start the people pipeline in Week 10.
- **Hard part 1: the tokenizer must run on the phone, in Kotlin.** LiteRT ships no tokenizer. WordPiece (BERT family: ArabicBERT, CAMeLBERT, MARBERT, HAYAA) is ~100 lines. **SentencePiece** (multilingual-E5, MiniLM, XLM-R, mmBERT, Gemma) has no ready Kotlin / Android implementation. Vocabulary trimming also re-maps token ids. The tokenizer is therefore a **third hard rule** next to language and license (MediaPipe's text tasks run WordPiece and SentencePiece models with attached metadata, but only for message-level classification, not a word head).
- **Hard part 2: a word-level head needs word-level teacher labels.** Qwen3Guard-8B labels the *message*; getting word spans from a generative teacher means prompting for the words and aligning them back to the text, which is messy and must be checked by hand.
- **Proposal.** Define a **minimum layer ②** that is "done" for the graduation product: **Arabic first**, **message level only** (the whole-message cover that FR-9 already allows), a **char n-gram linear model** as the baseline that needs no tokenizer, and one WordPiece encoder as the neural candidate. Word spans and English become stretch goals, reported as far as they got. Keep the full comparison table (M7) but with this smaller core.

### 1.4 The schedule is already behind

- Week 1 = Mon 12 Oct, so **today is the end of Week 2**. v1-a (Weeks 1–2) has not started; P0c step 1 (Week 2) has not started; the three streams are not yet assigned (roadmap §3, Phase 0).
- **Proposal.** Reset Week 1 to **Mon 26 Oct 2026** and keep the same 27-week shape, shortening v2 (Weeks 6–9) by one week if the deadline does not move. Record the reset in `asbuild.md`.

---

## 2. Gaps in the architecture document

| # | Gap | Why it matters | Proposal |
|---|---|---|---|
| 2.1 | **The cover store is not described.** Text, OCR and people all produce covers that must survive scrolling, be re-validated when a recycled view changes its text, expire when the node leaves the screen, and carry a state (pending / confirmed / peeked). | It is the heart of the service and the one structure all three paths share. | Design it before v1-b: one store keyed by (window id, node id, text fingerprint, span) with explicit states and lifecycle rules. |
| 2.2 | **Scroll following by delta is fragile.** `scrollDeltaX/Y` is reported only by some views and only since API 28. | During a fling, covers lag by one event interval whatever we do: the "floating blur" complaint from the competitor's reviews. | Re-read each tracked node's `getBoundsInScreen` on every scroll event instead of applying deltas. Say the lag honestly in the design and the report. |
| 2.3 | **Per-letter boxes will fail more often than expected.** Standard `TextView` and Compose `Text` support `EXTRA_DATA_TEXT_CHARACTER_LOCATION_KEY`; Flutter apps probably do not; Facebook and Instagram use custom text rendering. | Decides how often the whole-message fallback fires. | The v1-a logging exercise is essential (issue #14). Also **split a wrapped word's character boxes by line** before taking their union, or a word broken across two lines produces a cover across the whole paragraph. |
| 2.4 | **Normalization changes string offsets.** The normalizer maps symbols to spaces and collapses repeated letters, so offsets of the normalized string do not map to the original. | Wrong offsets put covers on the wrong letters. | Normalize **per token** and keep each token's original span; never normalize the whole string. Consider generating Arabic prefix / suffix forms **offline in `build_ar.py`** instead of stripping at runtime, so the builder stays the single source of truth and the NFR-2 test covers the inflections. |
| 2.5 | **Threading and coordinates are unstated.** Events arrive on the main thread; node traversal is IPC-heavy; a GPU delegate must be used from the thread that created it; node bounds are in *screen* space, the window picture is in *window* space, and the overlay has its own origin unless laid out to the full screen (status bar, cutout, rotation). | One week of bugs. | One short section in the app design: a single-slot "latest screen wins" worker for reading the tree, a model thread per model, overlay drawing on the main thread, one coordinate convention. |
| 2.6 | **OCR may need a second runtime.** C-7 says everything runs on LiteRT, but PaddleOCR's detection model has dynamic shapes and the Paddle → ONNX → TF → LiteRT conversion is unreliable. | v2 could stall on conversion. | Decide at P0d; ONNX Runtime Mobile (already used on the laptop) is the likely answer. Amend C-7 to "LiteRT or ONNX Runtime, on the phone". |
| 2.7 | **Keeping the GPU model warm.** Releasing the people model when the screen turns off costs a ~4 s GPU start on every unlock. | Four seconds of "everything covered" or "nothing checked" after every unlock. | Release only after a long idle (for example 10 min screen off); try the GPU delegate's serialization cache (issue #30) for the start-up cost at 640 too. |
| 2.8 | **"Where the screen changed" for v4 tiles** is derived from event bounds in the plan. | Event source bounds are coarse and sometimes missing. | A downscaled diff of two consecutive window pictures is cheap and reliable; use it for both tiles and the video policy (§1.2). |
| 2.9 | **False covers on UI.** Threshold 0.1 gave a 6% false alarm on person-free *photos*. Screens are full of icons and illustrations. | Random covers over buttons and logos until the real screenshot test set exists. | Measure on real screenshots in v3 (planned) and plan a suppression rule (minimum size, per-app allow-list, or a second pass at a higher threshold for tiny detections). |
| 2.10 | **Only one test phone.** SRS §2.5: "if it works here, it works on most phones." | True for model speed; **not** true for accessibility behaviour, overlays and background killing, where OEM differences are large. | Add a second phone from another maker (a team member's own) for v1-a logging and for the HyperOS-specific checks (#18, #34). |

---

## 3. Smaller points on the plan and documents

- **Module split.** Put the text filter in its **own pure-JVM Gradle module** (`:filter`) instead of a package inside `:app`. It costs nothing and enforces NFR-18 at compile time. Add a one-job GitHub Actions run of its tests, since three people share the repo.
- **Record and replay.** In v1-a, record real accessibility trees from the seven test apps as JSON and replay them through the filter on the laptop. This gives deterministic tests and the corpus for NFR-1 / NFR-2 at the same time. Do the same with window pictures for v2 / v3.
- **Debug inspector first.** Build a dev-only overlay that draws node bounds and shows the logged text. It answers issue #14 and is the fastest way to see what each app shares.
- **Chrome's accessibility filtering.** Chrome may hand a reduced tree depending on which event types and flags the service declares. Request the full set during v1-a logging; narrow later.
- **Stream B load** is heavy in Weeks 3–5 (list review, dataset building, teacher-label checking). Ship the swearing and sexual categories first, as the risk table already says.
- **Interim HAYAA-student** is research-only: fine for development, never in a build given to anyone outside the team.
- **Minor inconsistencies.** Investigation §9 quotes a 200 MB memory target while the SRS says 250 MB (NFR-9). Several documents still say "v1.1" (known). The 13 ms (Potter 2014) and Nielsen citations are flagged as from memory and still need checking before the report.

---

## 4. Proposed changes, with owners

| # | Change | Where | Stream | When |
|---|---|---|---|---|
| 1 | Reset Week 1 to Mon 26 Oct 2026; shorten v2 by one week if the deadline is fixed | `roadmap.md`, `asbuild.md` | all | This week |
| 2 | Re-baseline NFR-3 to a measured p95 target; state that plain text is not hide-first | SRS §6.2, `app-design-v1.md` §2 | A | Before v1-b |
| 3 | Add a **video policy** (strict or poll) to v3, with a battery measurement | `app-design-v1.md` §10, SRS F6, `roadmap.md` v3 | A + C | Design now, build in v3 |
| 4 | Define the **minimum layer ②** (Arabic, message level, n-gram baseline + one WordPiece encoder); tokenizer as a third hard rule | `investigation-android-v1.md` §3.5, `roadmap.md` v1 part 2, SRS FR-20 | C | Before P0c |
| 5 | Add the **cover store**, the threading model and one coordinate convention to the app design | `app-design-v1.md` (new §2.1–2.3) | A | Before v1-b |
| 6 | Scroll following by re-reading node bounds, not deltas; split per-letter boxes by line | `app-design-v1.md` §2 | A | v1-b |
| 7 | Per-token normalization with original spans; prefix / suffix forms generated offline | `app-design-v1.md` §2, `wordlists/build_ar.py` | A + B | v1-b / v1-c |
| 8 | `:filter` as a pure-JVM module; one CI job for its tests | project setup | A | v1-a |
| 9 | Debug inspector + tree recording and replay | v1-a scope | A | v1-a |
| 10 | Second test phone for v1-a logging | `roadmap.md` Phase 0 | all | v1-a |
| 11 | Amend C-7 after P0d (LiteRT or ONNX Runtime) | SRS §2.6 | C | Week 5 |
| 12 | Model release after long idle only; try the GPU serialization cache at 640 | `app-design-v1.md` §10 (v3 hook) | C | v3 |
| 13 | Fix the 200 / 250 MB mismatch; check the two citations | investigation §9, SRS | B | Any time |

Decisions taken on these points go to [`asbuild.md`](asbuild.md); anything left open becomes an issue in [`issue.md`](issue.md).
