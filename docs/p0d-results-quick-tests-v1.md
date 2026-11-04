# Quick Phone Tests: Boxes, Cover Gap, Window Picture, Text Accuracy

Date: 2026-11-04 · Phone: Xiaomi Redmi 12 (Helio G88, Android 15, 8 GB) · Test app: [`probe/`](../probe) (an accessibility service that logs counts only, never text)
Scope: four quick checks from the technical review, to know the plan works before building the app. Not full studies.

## 1. Bottom line

| # | Question | Answer |
|---|---|---|
| 1 | Do apps give per-letter boxes? | **Mostly yes.** Chrome, WhatsApp, TikTok, Telegram: yes. YouTube: partly. Facebook: no (whole item only). |
| 2 | How long is a word seen before the cover lands? | **New text: no gap seen.** **Scrolling: real gap**, covers stay at the old place while the list moves (review point 1 confirmed). |
| 5 | Does the window picture work, and does it include our covers? | **Works in all 4 apps, ~20–60 ms, our covers are not in it.** One picture per ~330 ms (rate limit). |
| 7 | Is a small text model better than the word list? | **Yes.** bert-mini-arabic 0.82 macro-F1 vs word list 0.65 on OSACT 2020. |

## 2. Test 1: per-letter boxes (`--es cmd boxes`)

The service samples the open app every 2 s, counts text items, and asks up to 5 visible ones for letter boxes ([log](../bench/results/probe_boxes.log)).

| App | Gave boxes / asked | Note |
|---|---|---|
| Chrome | 16 / 17 | |
| WhatsApp | 37 / 40 | |
| TikTok | 19 / 20 | |
| Telegram | 29 / 29 | |
| YouTube | 2 / 7 | many screens share descriptions only, no text |
| Facebook | 0 | no box support: only whole-item covers |

- One box request takes **~5–10 ms**.
- X and Instagram were not installed, so not tested.
- **Testing app by app does not scale.** Better: (a) the app checks at run time and falls back to covering the whole item when boxes are missing; (b) test by UI toolkit (Views, Compose, WebView, React Native, Flutter, custom such as Facebook's Litho) instead of by app; (c) if needed, an automatic sweep over all installed apps.

## 3. Test 2: cover gap (`--es cmd gap`)

Test screen: the word ZQXJ in pure magenta. The top line switches between "No message" and "New message ZQXJ here" every 1.5 s; below it a 400-row list to fling. The service covers every visible ZQXJ on every event ([log](../bench/results/probe_gap.log), [frame counter](../bench/gap_frames.py)).

| | Result |
|---|---|
| Cover update after an event | median **21 ms**, p95 37 ms, max 49 ms (246 updates) |
| New text (top line) | 4 screenshots at random moments: cover always on the word, never on "No message". **No gap seen.** |
| Scrolling | 34 times visible, 7.4 s in total, longest 2.2 s. Covers stay where the word was while the list moves. |

- The screen recording showed the top-line cover one state behind, but plain screenshots did not. That part is a recording artefact (`screenrecord` writes frames only on change). The scroll numbers come from the same recording, so treat them as **upper bounds**; the gap itself is clear to the eye.
- **Fix for scrolling** (review point 1): on a scroll event, cover the whole scrolling area at once, then put the exact boxes back when it settles.
- **Found by accident:** reinstalling or force-stopping the app leaves the service "enabled" in settings but not running. The real app must detect this and tell the user, or the filter silently stops.
- HaramBlur's accessibility service was also running on the phone during the tests.

## 4. Test 5: window picture (`--es cmd shot`)

The service draws a magenta test box over the app, then takes a picture of the app window: at once, again at once, again after 400 ms, then of the full display ([log](../bench/results/probe_shot.log)).

| App | First | Again at once | After 400 ms | Our box in window picture? | In full-display picture? |
|---|---|---|---|---|---|
| Chrome | ok, 26 ms | refused (code 3) | ok, 25 ms | no | yes |
| WhatsApp | ok, 21 ms | refused (code 3) | ok, 18 ms | no | yes |
| Telegram | ok, 57 ms | refused (code 3) | ok, 29 ms | no | yes |
| YouTube | ok, 19 ms | refused (code 3) | ok, 21 ms | no | yes |

- `takeScreenshotOfWindow` gives the **app without our covers**: the image model never sees its own black boxes, so no feedback loop. Use it, not the full-display picture.
- Code 3 = too soon (rate limit, ~333 ms). So pictures for the image model come at most **~3 per second**; the app must queue and skip, not retry at once.
- Picture is full size (1080 × 2460): the review's "shrink to 480 px before the model" still applies.

## 5. Test 7: text model vs word list (OSACT 2020, offensive or not)

bert-mini-arabic fine-tuned on the 7 000 training tweets, scored on the 1 000 dev tweets (test labels are not public) ([script](../bench/train_text.py), [log](../bench/results/text_train_osact.log)). CPU, ~6 min.

| Method | Macro-F1 | Offensive-F1 |
|---|---|---|
| Word list (680 Arabic words) | 0.649 | 0.467 |
| bert-mini-arabic, epoch 3 | **0.817** | **0.704** |
| Model OR word list | 0.664 | 0.530 |

- The model clearly beats the list. Combining them is worse: the list flags too much.
- Epoch 3 was picked on the same dev set, so 0.82 is slightly optimistic.
- OSACT is tweets labelled "offensive", not exactly our categories: this proves the model learns, not final accuracy.

## 6. Not done

- X and Instagram (not installed); toolkit-based test.
- The scroll fix (cover the scrolling area) is not built or measured.
- The other open tests (not in this batch).
