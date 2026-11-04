# App Design (v1, with hooks for v1.1–v6)

Date: 2026-10-07 · Status: **agreed in design review, for team review** · Scope: the Android app.
Requirements: SRS v3.0 ([`srs-en.pdf`](srs-en.pdf)). Background and sources: [`investigation-android-v1.md`](investigation-android-v1.md). Plan: [`roadmap.md`](roadmap.md).

---

## 1. Decisions in one table

| Topic | Decision | Why |
|---|---|---|
| Language | **Kotlin only** | The team knows Kotlin. The accessibility service and covers must be native anyway. Rust was considered for the matcher, but a word lookup takes under 1 ms in Kotlin, and Rust would add the NDK and a JNI bridge. |
| Structure | **One app, one accessibility service** (approach A). The text filter is a plain-Kotlin package with no Android code. | Least setup. The filter can still be tested on the laptop. A separate process for models is reconsidered in v3 only if the people model crashes or stalls. |
| Screens | **Jetpack Compose + Material 3**, Arabic right-to-left and English, following the phone's language | Modern, built-in RTL |
| Android versions | **minSdk 26** (Android 8.0: per-letter text boxes). Target: the latest stable SDK. Picture features (v2+: text in images, people, video) only on **Android 14+**; no fallback for older phones for now. | §2 of the investigation |
| Covers | **One full-screen, touch-through accessibility overlay** that draws every cover | Fewer windows, faster; a trusted accessibility overlay may be fully opaque and let touches through |
| Peeking | **Peek one item (FR-23).** The accessibility button starts a 5 s peek mode: covers become tappable (outlined); tapping one shows that item only, until it leaves the screen. Pause (5/15/60 min) shows everything. Off in self-control mode (FR-25, future). | Covers let touches pass, so they cannot catch normal taps; the accessibility button is a separate, built-in signal. Changed 2026-10-21 (was "none in v1") |
| Languages | **Language packs**: the user picks one (default: phone language) or two. Only chosen packs use RAM. Text is routed to a pack by its script. | Smaller and faster; each language can use its best model |
| Text filtering | **Layer ① word list (v1)**; **layer ② our own small model per language (v1.1)** for context and offensive words | Investigation §3.5 |
| Privacy | **No internet permission.** Screen text is processed in memory only. | Promise to users; looks less like malware to Play Protect |
| Install | APK over ADB for development and demo; Google Play later with the team's **existing Google Play developer account** | Android developer verification (§3 below) |

---

## 2. Architecture

```
app/
 ├─ filter/      plain Kotlin, no Android            (tested on the laptop)
 │   ├─ Normalizer   same rules as wordlists/build_ar.py
 │   ├─ Tokenizer    split into words, keep character offsets
 │   ├─ Router       split text by script → language pack
 │   ├─ WordList     load words.tsv; whole-word and phrase lookup
 │   └─ Matcher      text → [ (start, end, category) ]
 ├─ model/       (v1.1) TextModel interface: text → categories + offensive word spans
 │               one implementation per pack (LiteRT); cache by message fingerprint
 ├─ service/     MaskingService (AccessibilityService)
 │               events → read visible text → filter (+ model) → word boxes → overlay
 ├─ overlay/     CoverOverlay: one full-screen TYPE_ACCESSIBILITY_OVERLAY, draws boxes
 ├─ ui/          Compose: setup, home, settings, try-it
 ├─ settings/    DataStore
 ├─ status/      notification + periodic health check
 └─ tile/        Quick Settings tile
assets/packs/<lang>/   words.tsv  (v1.1: model.tflite, tokenizer.json, thresholds.json)
```

### One screen change, step by step

1. An app shows new text (scroll, new page, new message). Android sends an event. The service waits until scrolling settles (event timeout) and keeps only the latest screen.
2. It reads the **visible** text items, skipping input boxes (FR-11), its own app, system UI, and skipped apps.
3. **Router** splits the text by script and sends it to the chosen packs only.
4. **Layer ①**: Normalizer → Tokenizer → Matcher finds listed words and phrases.
5. **Layer ② (v1.1)**: only for messages with context-dependent words, or every new message in strict mode. Messages already checked come from the cache. Messages of one screen go to the model in one batch, at short input lengths (16 / 32 / 64 tokens).
6. For each hit, the service asks Android for the **word's screen box** (per-letter boxes). If the app does not provide them, the **whole message** box is used.
7. **CoverOverlay** redraws all covers.

---

## 3. Platform facts that shape the design

| Fact | Design answer |
|---|---|
| **Restricted settings** (Android 13+, stricter in 15): an app installed from an APK cannot turn on accessibility until the user allows "restricted settings" | Setup step 5 shows how: App info → ⋮ → "Allow restricted settings" |
| **Developer verification**: from 30 Sep 2026 in four countries, worldwide in 2027, certified phones install only apps from verified developers; ADB installs are exempt; a student / hobbyist "limited distribution" account exists | ADB for development and demo; the team already has a verified Google Play developer account (an app was published on 2026-10-07) |
| **Android 17 Advanced Protection Mode** (opt-in) removes accessibility access from apps that are not accessibility tools | We are not an accessibility tool and do not claim to be. Detect the mode (`AdvancedProtectionManager`) and explain it on Home |
| **Play Protect** scans sideloaded apps; Android 17 watches for misuse of accessibility overlays | No internet permission, minimal permissions, clear consent screen, honest description. Test early for warnings |
| **LiteRT CompiledModel API** (CPU / GPU / NPU, Kotlin) | Runtime for v1.1, v2 (OCR) and v3+ models |
| **Google SafetyCore / ContentSafetyManager** (on-device sensitive-image classifier, API in development) | Watch only; maybe an extra check for v3+ |

Sources: investigation §2, §8, §11, and research-methods §9.

---

## 4. Inside the app (screens)

### First run: setup (one step per screen, with a progress bar)

| # | Screen | Content |
|---|---|---|
| 1 | Welcome | What the app does. "Nothing leaves your phone; the app has no internet access." |
| 2 | Languages | The phone's language ticked; add the other if needed (FR-21) |
| 3 | What to hide | Swearing / sexual words / insults / blasphemy (all on); cover style: word only or whole message (FR-9, FR-10) |
| 4 | Consent | In plain words: what the accessibility permission lets the app see; nothing is saved or sent (FR-1) |
| 5 | Turn on access | Button to the accessibility settings. If blocked: how to allow restricted settings. The app notices when access is on and moves on by itself. |
| 6 | Xiaomi only | Autostart on; battery "No restrictions" |
| 7 | Notifications | Permission (Android 13+), for the status notification |
| 8 | Try it | Sample text with bad words, to see the covers working |

### Home

- Big status: **On / Paused (until 14:30) / Off / Problem**, with a switch.
- **Pause**: 5 min / 15 min / 1 hour.
- Active languages; **today's count** of covered words (a number only).
- **Warning cards**: access turned off, battery limits, Advanced Protection on, a pack failed to load.

### Settings

Languages · What to hide · Cover style and colour · **Skipped apps** (searchable) · About and privacy. Added later: **Strictness** (v1.1, from the model's confidence) and **People** (v3+).

**Not included:** accounts, cloud, statistics beyond counts, password or lock (not planned in the SRS).

---

## 5. Outside the app

### Covers

- **Solid block, slightly rounded corners**, 2–4 dp larger than the word on each side. No text or icon on word covers.
- Colour: neutral grey by default; the user can choose another colour.
- "Whole message" mode covers the message's box.
- **Touches pass through.** A cover opens only through peek (FR-23): accessibility button, then tap that cover. Uncovered items are kept in memory only and covered again when they leave the screen.
- **Context words** (list entries marked *context*) are covered at once; the cover is removed only if the text model says the message is clean above the strictness level (FR-24).
- Covers **move with scrolling** (FR-3) and are removed at once on pause, off, or when a skipped app opens; on resume the screen is checked again immediately.
- Positions come from Android's per-letter boxes, so right-to-left text needs no special handling.

### Status notification (silent, while the filter runs)

| State | Text | Buttons |
|---|---|---|
| On | "Filter is on · Arabic · 12 words covered today" | Pause 15 min · Turn off |
| Paused | "Paused until 14:30" | Resume |
| Problem | "Filter stopped: tap to fix" | Opens the fix screen |

### Quick Settings tile

Tap: on / off. Long-press: open the app. Label: **On / Paused 14:30 / Off** (tile subtitle, Android 10+).

**Not included:** home-screen widget, sounds, vibration, pop-ups over other apps.

---

## 6. Data and storage

| What | Where | Rule |
|---|---|---|
| Language packs | APK assets `packs/<lang>/` | `words.tsv` is generated from the reviewed `wordlists/` by a build script; v1.1 adds `model.tflite`, `tokenizer.json`, `thresholds.json` |
| Settings | DataStore | on/off, languages, categories, cover style and colour, skipped apps, paused-until |
| Today's count | DataStore | A number only; reset daily |
| Checked messages | Memory only, ~2 000 fingerprints | Never written to disk |
| Logs | Debug builds only | Release builds never log screen text |

---

## 7. Errors (fail toward hiding, and visibly)

| Problem | Behaviour |
|---|---|
| No per-letter boxes from an app | Cover the whole message |
| Pack model fails to load (v1.1) | Word list only for that language; warning card |
| Pack word list fails to load | That language off; notification shows the error |
| Overlay cannot be drawn, or service stopped | Notification "stopped: tap to fix"; warning card |
| Advanced Protection on | Setup and Home explain why the filter cannot run |

---

## 8. Testing (lean)

| Level | What |
|---|---|
| Laptop (JUnit) | Normalizer, Tokenizer, Router, Matcher: table-driven Arabic and English cases. **One shared test-vector file** (input → expected normalized form) is used by both the Kotlin tests and `wordlists/build_ar.py --test`, so the list builder and the app clean text identically. |
| Phone | NFR-1, NFR-2, NFR-3 and battery measurements (research-methods §4.6); P0c benchmarks for v1.1 |
| Not done | UI / screenshot tests, heavy end-to-end tests (the team checks the look by hand) |

Project setup: Kotlin + Gradle (Kotlin DSL), one app module. No CI or lint tooling until a need appears.

---

## 9. To verify early in v1-a (assumptions not yet tested)

| Assumption | How we check | If wrong |
|---|---|---|
| The status notification shows when the service has stopped | Kill the app process on the Redmi 12 and watch the notification | Make the service foreground if Android allows it for accessibility services, or add a 15-minute health check (WorkManager) that switches the notification to "stopped" |
| Popular apps share their text and per-letter boxes | Log what the service sees in Chrome, WhatsApp, Facebook, X, YouTube, Instagram, TikTok | Whole-message covers for that app; note it in the results |
| Covers do not slow scrolling (NFR-7) | Scroll with the overlay on and off; watch frame drops | Fewer redraws: only when covers change |
| Our covers appear in the user's own screenshots | Take a screenshot with covers visible | Record it as a limit |
| Restricted-settings flow on the Redmi 12 (HyperOS) | Install the APK from a file and follow setup step 5 | Adjust the instructions |

---

## 10. Later versions (hooks only, not built in v1)

| Version | Hook in this design |
|---|---|
| v1.1 | `model/` TextModel per pack; Strictness setting; files added to `packs/<lang>/` |
| v2 | Window picture (Android 14+), OCR model; words found in images go through the same `filter/` and are covered by the same CoverOverlay |
| v3–v5 | People model, mask covers drawn by the same CoverOverlay; People settings; possibly a separate process for the model |
| v6 | Video: the method chosen in the roadmap (tracking between checks, screen capture during video, or strict mode) |
| Later | Arabizi pack; a short product name (issue #4) |
