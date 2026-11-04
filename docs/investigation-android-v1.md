# Technical Investigation, Android v1

**Real-time, system-wide hiding of bad-language text and people on an Android phone**
Scope: Android, no root. Linux is paused as plan B ([`investigation-linux-v1.md`](investigation-linux-v1.md)).
Date: 2026-10-06 (updated: text first) · Status: investigation. Phone test results so far: [`p0-results-android-v1.md`](p0-results-android-v1.md)

---

## 0. Verdict (short)

| Question | Answer |
|---|---|
| What comes first? | **v1 hides bad-language text** (Arabic and English) with a word list. **v1.1 adds our own small AI text model** on the phone, which understands context and points at the offensive words (§3.5). **v2 reads text inside images** (OCR) with the same window picture the people stages need. People follow in three steps: **big (v3), medium (v4), small (v5)**, then **video (v6)**. Text is the easiest start: it builds the whole app that the later stages reuse (§3). |
| Is it possible on a normal (not rooted) phone? | **Yes, with limits.** An app cannot sit inside Android's screen drawing the way the Linux plugin could. It has to **look at the screen from the side and draw a cover on top**. |
| Which Android parts? | One **accessibility service** does all of it. It hears when the screen changes (scroll, new page, app switch). It takes a picture of the **app's window only** (Android 14+). It draws the covers in a **trusted accessibility overlay**. No fallback for Android 13 and older for now (decided 2026-10-18). |
| Can we still "hide first" (never show unchecked content)? | **Mostly, on Android 14+.** The window picture does not include our own covers, so we can cover first and check under the cover. There is still a short gap between the app drawing and our cover going up (one accessibility event). It is **not measured yet** and is the first thing to measure in v1 (for text) and v3 (for people). On older Android, hide-first is not possible (§5). |
| Is the phone fast enough? | **For text and big people, yes.** Redmi 12, people model at 640 px: **GPU ~205 ms per check** (189 ms over 15 minutes non-stop), best CPU setting 277 ms (§6). Tiles for smaller people do not fit on every change, so they run only where the screen changed. |
| Is accuracy good enough? | **Large people yes, small people no.** Same picture as on Linux. On fake phone screens, one pass hides 24–26% of small people, and 3 tiles hide 52–54%. Details in the results doc. |
| Biggest risks | Text: (1) the final Arabic word list must be built by the team (free lists are only a start), (2) text inside images and videos needs OCR (v2), whose phone speed is not measured yet. People: (3) the phone may be too slow for tiles, (4) small people, (5) video (v6). Both: (6) Android and Xiaomi limits on background apps. |

**The main change from Linux:** on Linux we owned the screen drawing, so "never show unchecked content" was easy. On Android we do not. The phone also has about **one tenth** of the laptop's speed. The design below is built around those two facts.

### Release order

| Version | Hides | Why this order | Today |
|---|---|---|---|
| **v1** | **Bad-language text**: swearing, sexual words, insults, blasphemy, in standard Arabic and English | No AI model needed. Fast and light on battery. Builds the app: service, cover, scroll tracking, settings. | Designed (§3). Not built. |
| **v1.1** | **Context**: our own small text model as a second layer | A word list cannot see context (§3.5) | Planned |
| **v2** | **Text inside images**: memes, thumbnails, subtitles burned into videos | Builds the window picture that the people stages reuse; PaddleOCR has an Arabic mobile model | Planned; phone test P0d first |
| **v3** | **Big people** (taller than about 96 px on screen) | The model already hides 85–95% of them | Model tested offline |
| **v4** | **Medium people** (about 32–96 px) | Needs the closer check in tiles, so it needs a faster phone setup | 60–76% offline, 87–89% with tiles |
| **v5** | **Small people** (under about 32 px) | Needs our own training on phone screenshots | 24–27% offline, 51–54% with tiles |
| **v6** | **Video**: people in videos while they play | 3 pictures per second cannot follow movement; needs its own method | Needs research |

Each version adds to the one before. v3 still covers any small person it happens to find, but it only **promises** big ones.

---

## 1. Target phone (Redmi 12)

```
Phone  Xiaomi Redmi 12 (4G)          Screen  6.79", 1080 × 2460, 90 Hz
Chip   MediaTek Helio G88 (12 nm)    CPU     2 × Cortex-A75 2.0 GHz + 6 × Cortex-A55 1.8 GHz
GPU    Mali-G52 MC2 (small)          OS      shipped Android 13 (MIUI 14), update to Android 14 (HyperOS)
```

Source: GSMArena / mi.com specs [1].

What this means:
- Only **2 fast CPU cores.** The other 6 are slow. Using 4 threads instead of 2 only helps by about 1.6× (measured: 463 → 295 ms).
- The **GPU is small**. LiteRT can still run the model on it, but nobody has measured that yet.
- **Which Android version is on the test phone matters a lot** (the window picture needs Android 14, §4). Check: Settings → About phone.

---

## 2. What a normal Android app can and cannot do

On Linux, the app could sit **inside** the program that draws the screen. On Android that program is **SurfaceFlinger**, a system service. Normal apps cannot change it. Everything below is what is left.

| Option | How it sees the screen | How it covers | Problems | Verdict |
|---|---|---|---|---|
| **A. Screen capture + app overlay** | MediaProjection (like screen recording) | Normal "draw over other apps" window | Asks for permission **every session** (Android 14+) [2]. Our covers show up in our own capture. **A see-through overlay is capped at 80% opacity**, so 20% of the person still shows through [3]. | ❌ The 80% cap alone rules it out. |
| **B. Accessibility service only** (Android 14+) | `takeScreenshotOfWindow`: a picture of **one app's window**, without our covers [4] | Accessibility overlay: trusted, fully opaque, touches pass through [3] | Max **3 pictures per second per window** (one every 333 ms) [5]. Needs Android 14. | ✅ **Main path.** |
| **C. Screen capture + accessibility overlay** | MediaProjection | Accessibility overlay | Our covers appear in the capture (see below). Permission prompt each session. | ⏸ Not planned for now (Android 14+ only, 2026-10-18). May return for video only (v6). |
| D. Root (Magisk / LSPosed hook into SurfaceFlinger) | Inside the screen drawing, like Linux | Inside the screen drawing | Only rooted phones. Hard. Breaks with updates. | ❌ Not v1 (maybe a "pro mode" later) |
| E. Custom ROM | Inside the system | Inside the system | Users would have to reflash their phone | ❌ Not v1 |

### Why our own covers in the capture are a real problem (option C)

When we cover a person, the next capture shows **our cover**, not the person. The model sees no person there, so it would remove the cover, then see the person again, and so on (flicker). Ways around it:
- **Keep a cover until the content under it moves or changes.** The accessibility service tells us when the app scrolls, and on most apps by how much. Covers move with the scroll. They are removed only when that part of the page leaves the screen or the app changes.
- **Do not try to hide the cover from the capture.** On a MediaTek phone, others tried `FLAG_SECURE`, `setPrivacySensitive` and `setSkipScreenshot`. None of them worked cleanly: the screen went black or the cover was still captured [6].

Option B does not have this problem, because a window picture only contains the app.

---

## 3. v1: hiding bad-language text

### 3.1 How it works

Most apps already tell Android what text is on the screen, so screen readers can read it aloud. Our accessibility service can read the same text. **No picture and no AI model are needed.**

```
┌──────────────── Our app (same accessibility service) ──────────────────────┐
│  1. EVENTS   content changed / scrolled / app switched                     │
│  2. READ     walk the visible screen items, take each item's text          │
│  3. CLEAN    normalize the text (rules in §3.3)                            │
│  4. MATCH    look each word and phrase up in the bad-word list             │
│  5. LOCATE   ask Android for the exact screen box of the bad word          │
│              (character boxes, Android 8.0+ [9]); if the app does not      │
│              give them, use the whole message's box                        │
│  6. COVER    solid block over the word, or over the whole message          │
│              (the user chooses in settings)                                │
└────────────────────────────────────────────────────────────────────────────┘
```

- **Fast.** A word-list lookup takes well under a millisecond. The slow part is Android delivering the event. That gap is **not measured yet** and is the first thing to measure in v1-b (§10).
- **No hide-first for text.** Checking is so fast that covering everything first would make covers flash all the time. The cover appears right after the text, after about one event delay.
- **Text the user is typing** (input boxes) is **not covered** by default. It is the user's own text.
- **Same cover and scroll tracking as the people stages.** v1 builds them, and v3–v5 reuse them.

### 3.2 What v1 can and cannot see

| Text | v1? | Why |
|---|---|---|
| Normal app text: posts, comments, chats, titles, buttons | ✅ | Apps give it to accessibility |
| Web pages in Chrome, and apps that show web pages (WebView) | ✅ | Chrome gives page text **and per-letter boxes** to accessibility (checked in Chromium's source [13]). Other browsers (Firefox, Samsung, Opera) must be **tested in v1-b**. |
| Text the app draws itself (many games, some custom apps) | ❌ | Not given to accessibility |
| **Text inside images and videos** (memes, thumbnails, burned-in subtitles) | ❌ (v2) | Needs OCR (reading text from pixels). Google's on-device OCR (ML Kit) **does not support Arabic** [10]. **v2: PaddleOCR** (PP-OCRv5 Arabic mobile model, about 8 MB [16]). A team member has worked with PaddleOCR and plans to contribute Arabic improvements to it. |

### 3.3 Word list and matching

**Languages:** standard Arabic and English. **Categories:** swearing, sexual words, insults, blasphemy. Each list entry is tagged with its category, so the user can turn categories on and off.

| Source | Size | Note |
|---|---|---|
| **LDNOOBW V2, Arabic** [14] | 1 284 entries: **348 in Arabic script**, 936 Arabizi | **CC0** (free to use). The best free start for Arabic. The Arabizi part is useful after v1. |
| **Attia Arabic lexicon** (2025) [15] | about **372 Arabic terms**, sorted into categories with English notes | Built from human-labelled offensive datasets (mostly Egyptian and Levantine). Categories match ours well. **No license file**: cite it, and **ask the author** before copying entries into our list. |
| LDNOOBW English list [11] | 403 entries | CC-BY-4.0, so the report must credit it. It mixes categories and includes some medical and neutral words, so **the team must review it**. (V2 has 13 000 English entries, which is too noisy.) |
| LDNOOBW (first version), Arabic [11] | only 38 entries | Too small, superseded by V2 |
| Arabic offensive-language research data (OSACT 2020, 10 000 labelled tweets [12]; Mubarak 2017 obscene / offensive / clean tweets [17]) | — | For **testing** the list on real comments |
| Mubarak 2017 obscene word and hashtag list [17] | 415 entries | Still downloadable from QCRI. Free for research. |
| 4troDev profanity.csv, Arabic | 48 entries | MIT |

**All of these are already combined** in [`../wordlists/ar_combined.tsv`](../wordlists/ar_combined.tsv): **1 906 unique terms, 947 in Arabic script**, each tagged with its sources (see [`../wordlists/README.md`](../wordlists/README.md)).

**The team still builds the final Arabic list**: the free lists are a start, but they mix dialects, contain words that are only offensive in context, and are not sorted into our four categories. Plan: start from LDNOOBW V2 (Arabic script) → add terms after reading Attia's categories → keep standard Arabic only for v1 → tag each entry with one of the four categories → test (§3.4).

**Normalization (before matching)** catches spelling tricks:
- Arabic: remove tashkeel (diacritics) and tatweel (ـ). Make أ إ آ → ا, ى → ي, ة → ه.
- Collapse repeated letters: "كلبببب" → "كلب", "shiiit" → "shit".
- English: lowercase, and map look-alike symbols (`@`→a, `$`→s, `0`→o, `1`/`!`→i).
- Remove symbols and spaces placed inside a word ("s.h.i.t", "ك ل ب"). This is **later**: it risks false matches.

**Matching rules:**
- **Whole words only**, after normalization. So "class" does not match "ass". This is a known problem in word filters (the "Scunthorpe problem").
- Arabic words take prefixes and suffixes (ال، و، ب، ك، ـه، ـها، ـهم...). Each list entry stores its root form, and the matcher strips common prefixes and suffixes first.
- **Phrases** (several words) are needed for blasphemy and some insults, because the single words are often normal words.
- **Insults depend on context.** "حمار" (donkey) is a normal word in a story about animals. Insults therefore get their own on/off switch and a **stricter list** (only words that are almost always insults).
- **Second layer: a small AI model** (§3.5). A word list cannot see context, so v1.1 adds an on-phone model that reads the whole message.

### 3.4 How we measure v1

| Metric | How | Target |
|---|---|---|
| Bad words hidden | Test set of real comments (OSACT tweets + English comments + our own screenshots) | ≥ 95% of listed words |
| False covers | Clean text: news, Quran, schoolbooks, normal chats | ≤ 1 false cover per 1 000 clean words |
| Gap before the cover | Screen recording on the Redmi 12 (v1-b) | ≤ about 3 frames (≈ 33 ms) |
| Battery | 30 minutes of scrolling, filter on vs off | Small difference (to be measured) |

### 3.5 Second layer: our own small AI text model (v1.1)

**Why a model.** A word list misses three things: words whose meaning depends on context (كلب، حمار، كافر in a story, the news or the Quran), insults that contain no "bad word" at all, and new or creatively spelled words. A model reads the whole message. Most models only say whether a **message** is offensive, not **which words**. Finding the words is a known research task, *toxic spans detection* [38]. We need the words, to cover them.

**Two layers, both on the phone:**

```
every new message ─► ① WORD LIST (<1 ms) ── hard bad word? ──► cover the word at once
                        └─ contains a "depends on context" word, or (strict mode) any new message
                               ─► ② OUR SMALL MODEL (target ≤ 50 ms) ─► typed answer:
                                      message: clean / swearing / sexual / insult / blasphemy + confidence
                                      words:   which words are offensive
                                  ─► above the threshold for that category? cover the words (or the message)
results are remembered per message text, so scrolling back does not re-check
```

The typed answer follows the idea of "System One" decision models such as **Jev** (TypeSafe AI, Sep 2026) [28]: return a fixed choice with a confidence, fast, instead of free text.

#### Language packs: one model per language

The user chooses the language(s) to filter in the settings: **one by default** (the phone's language, Arabic or English), **two if needed**. Each language is a **pack**:

```
pack = word list (that language) + tokenizer + model file (.tflite) + thresholds per category
```

- **Only the chosen packs are loaded into RAM.** All packs ship inside the APK, because the app has no internet permission to download them. The APK is a bit bigger, but RAM, which is what matters on the phone, only holds the chosen ones.
- **Each pack can use a different model**: whichever model is best and lightest for that language in our measurements (P0c). For example, an Arabic-only model for Arabic and a small English model for English. All packs use the same app code through one interface (text in → categories and offensive words out), so swapping a model does not change the app.
- **One-language models are smaller.** Each pack's dictionary is trimmed to one language, so it holds fewer tokens than a bilingual one [41].
- **Routing by script, not by a language model.** Arabic letters and Latin letters sit in different Unicode ranges, so the app sends each piece of text to the right pack with a simple character check, at almost no cost. A message that mixes both is split by script. Arabizi (Arabic in Latin letters) needs its own pack later.

#### Efficiency: more than shrinking

What matters is RAM, ms and CPU/GPU on the phone. Shrinking the model is only one of three groups of methods. Each method is measured on its own in M7 (an ablation study).

| Group | Method | Saves |
|---|---|---|
| **Do less work** | **Cascade**: the word list (<1 ms) first; the model only on messages with context-dependent words, or on all new messages in strict mode | Most model runs |
| | **Cache by message text**: a message already checked is never checked again (scrolling back, repeated posts) | Repeated runs |
| | Only **new, visible** text. Skip input boxes, our own app, system UI, and skipped apps | Runs |
| | **Wait for the scroll to settle** (Android's event timeout), and drop stale work (only the latest screen counts) | Runs during fast scrolling |
| | **Routing by script**: the Arabic model sees only Arabic text | Runs, RAM |
| | **Small model first, bigger model only when unsure** (two-tier cascade); later, stop at an early layer when confident (early exit) | ms on easy messages |
| **Make each run cheaper** | **Short inputs**: messages cut into pieces of at most 64 tokens, fixed sizes (16 / 32 / 64), no padding to 256 | ms (work grows with tokens) |
| | **Batch** all new messages of one screen into one model call | ms per message |
| | **int8 / fp16 quantization**, checked against the float model (the full-int8 people model once found nobody, see results doc) | RAM, ms |
| | Fewer or narrower layers (distillation), pruning | RAM, ms |
| | **Pick the hardware by measurement**: CPU on the 2 fast cores, GPU, or NNAPI. Tiny models are often fastest on CPU; GPU has a start-up cost | ms, battery |
| | **Memory-mapped model files**: LiteRT maps the file, so only the parts in use (for example the Arabic rows of a dictionary) take real RAM [48]. Measure real RAM per process, not the file size | RAM |
| | Keep the model loaded only while the screen is on; release it when idle | RAM |
| **Use a cheaper kind of model** | **Classic classifier**: character n-grams + a linear model (SVM or logistic regression). An SVM + neural-network combination **won the OSACT 2020 Arabic offensive task (F1 90.51%)** [42]. A few MB, well under 1 ms | Almost everything; no context beyond n-grams |
| | **Static embeddings (Model2Vec)** [43]: turn a sentence model into a lookup table plus averaging, "up to 500× faster on CPU". Ready-made: potion-multilingual-128M (MIT, 101 languages), and Zarra for Arabic (MIT) [44]. We can also distil our own from any sentence model. | ms, RAM; weaker on word order |
| | **Sentence embedding + small head** (e.g. EmbeddingGemma [45], multilingual-E5 [47]) with cached embeddings | ms |

#### Candidates (all measured, none excluded by guesswork)

**Hard rules only:** the model must have the language in its dictionary, and its license must allow our use. Everything else is decided by measurement. Numbers are from Hugging Face (checked 2026-10-07 [49]); "working layers" is the part left after trimming the dictionary, which sets the RAM floor and most of the time.

| Group | Model | Total | Dictionary | Working layers | License | Languages |
|---|---|---|---|---|---|---|
| Classic | char n-gram + linear model (ours) | < 5 M | — | — | ours | any |
| Static | Model2Vec: potion-multilingual-128M / Zarra (Arabic) [44] | 128 M / 64 M | almost all | none (lookup + average) | MIT | 101 / Arabic |
| Tiny, Arabic | ArabicBERT-mini / -medium | 12 M / 42 M | 8 M / 16 M | **3 M / 26 M** | not stated | Arabic |
| | HAYAA-student [18] | 9 M | 6 M | **3 M** | research | Arabic |
| Small, multilingual | **multilingual-E5-small / multilingual-MiniLM** [47] | 118 M | 96 M | **22 M** | MIT / Apache | 100+ |
| | mmBERT-small [33], multilingual-toxicity-small [37] | 140 M | 98 M | 42 M | MIT / Apache | 1 800 |
| | DistilBERT multilingual | 135 M | ~92 M | ~43 M | Apache | 104 |
| Base, Arabic | CAMeLBERT-mix [40] / AraBERTv02 / MARBERTv2 [39] | 110–163 M | 23–77 M | ~86 M | Apache / ? / research? | Arabic |
| Base, multilingual | XLM-R base, mDeBERTa-v3, gte-multilingual | 279–305 M | ~192 M | 87–113 M | MIT / Apache | 100+ |
| | **Laya-multilingual** [31] | 322 M | 197 M | 125 M | Apache | 100+ |
| | **EmbeddingGemma** [45] | 308 M | ~200 M | ~100 M | Gemma terms | 100+ |
| Small generative | **Gemma 3 270M** [46] | 270 M | 170 M | 100 M | Gemma terms | 140+ |
| | LFM2-350M | 354 M | 67 M | 287 M | LFM license | incl. Arabic |
| | Qwen3Guard-Stream-0.6B [32] (labels every token) | 0.6 B | 156 M | ~440 M | Apache | 119 |
| Dropped (hard rule) | Von, SmolLM2 | — | English dictionary only | | | |

Teachers (laptop or Colab only, several GB of RAM): Qwen3Guard-8B [32], Laya [31], Von / Kev / GLiNER2.5-Decide [30]; Jev [28], [29] only if its terms allow. FanarGuard [36] (Arabic, cultural context) is a reference for what Arabic users consider harmful.

**Shrinking a 100-language model to one language (vocabulary trimming).** In mmBERT-base, which Laya-multilingual is built on, **197 M of the ~307 M parameters are the dictionary** (256 000 tokens for 1 800 languages). Vocabulary trimming deletes unused tokens and, per Ushio et al., keeps the original performance without retraining [41]. A first count on a small sample used **only 4 276 distinct Arabic + English tokens, 1.7% of the dictionary**; the real number comes from counting over the full training data. Trimming saves RAM and disk, not time: time comes from the working layers and the input length. And because LiteRT memory-maps the file [48], an untrimmed dictionary may cost less real RAM than its size suggests: P0c measures it.

#### P0c: choosing the model for each pack (two steps)

| Step | What | Cost |
|---|---|---|
| 1. Phone test | Export every candidate (trimmed to one language) to LiteRT; on the Redmi 12 measure **real RAM of the process, p50/p95 ms per message at 16 / 32 / 64 tokens, CPU 1/2/4 threads vs GPU**, battery temperature. No training needed for this. | ~2–3 days |
| 2. Quality test | Quick fine-tune of the candidates that pass step 1 (NFR-13) on a small dev set per language; measure F1 and false covers | ~1 week |

The pack's model is the best one that passes step 1. Different languages may end up with different models.

**Evidence that a small model can be good:** HAYAA-student keeps 96.7% agreement with a teacher 68× larger [18]; on ArabicDialectSafety (25 071 human-labelled Arabic texts, six varieties including standard Arabic) a fine-tuned small encoder (MARBERTv2 [39]) reached macro-F1 0.95 and beat larger generative models [34]; in the ArGuard 2026 shared task the best Arabic systems were also fine-tuned models [35].

**Recipe (teacher → student):**

| Step | What |
|---|---|
| 1. Data | Arabic: OSACT 2020 (10 000 tweets) [12], Mubarak 2017 [17], the standard-Arabic part of ArabicDialectSafety [34]; sentences that contain words from our list; clean text (news, Quran, schoolbooks) as negatives. English: comments with and without listed words. |
| 2. Teacher labels | Big open models on the laptop or Colab (Qwen3Guard-8B [32], Laya [31]; Jev or another API only if its terms allow training on its answers) answer our typed questions: offensive? which of the 4 categories? which words? Majority vote. **The team checks a sample by hand** and we measure agreement (Cohen's kappa). |
| 3. Student, per language | The model chosen in P0c for that language pack, trimmed to that language, fine-tuned on our labels (distilled from the teachers), with fewer layers if needed. Neural students get two heads: message category, and offensive-or-not for every word. |
| 4. Phone | int8 / fp16 → LiteRT (`.tflite`), CPU or GPU, plus the efficiency methods above. Target per pack (NFR-13): real RAM ≤ 100 MB, ≤ 50 ms per message (p95), at most about one CPU core busy while checking. |
| 5. Compare | Same test set per language: word list only · classic n-gram model · Model2Vec · HAYAA-student · multilingual-toxicity-small · trimmed models before fine-tuning · **our model** · the teachers. Report F1 per category, word-level F1, false covers per 1 000 clean words, and on the Redmi 12: real RAM, ms per message, CPU/GPU use. Plus the ablation: the effect of each efficiency method. |


---

## 4. People (v3–v5): proposed design (option B)

```
┌──────────────── Our app (one accessibility service) ──────────────────────┐
│                                                                           │
│  1. EVENTS   scroll / content changed / app switched                      │
│              → put a cover over the changed area at once  (hide first)    │
│                                                                           │
│  2. LOOK     takeScreenshotOfWindow(app window)   max 3/s, no covers in it│
│              (Android ≤13: MediaProjection frame, covers in it, §2)       │
│                                                                           │
│  3. CHECK    LiteRT (TFLite) model: yolo26n-seg → people masks            │
│              + our own NMS step (the exported model does not include it)  │
│                                                                           │
│  4. COVER    accessibility overlay: pixelate/solid over each person,      │
│              mask made a bit bigger, remove the "checking" cover          │
│                                                                           │
│  memory only · no internet permission · no screenshots saved              │
└────────────────────────────────────────────────────────────────────────────┘
```

Key choices:
- **One app, one service.** No server and no internet. The phone does everything.
- **Event-driven.** Nothing happens while the screen is still, which keeps battery use near zero when idle.
- **Opaque cover, not a light blur.** The same rule as on Linux: a light blur still shows the body shape.
- **Model format:** ONNX → LiteRT (`.tflite`), already exported (`bench/export_tflite.py`). The same model family as the Linux tests, so the accuracy numbers carry over.
- **Covers follow scrolling.** Scroll events carry how far the page moved, so covers move with it. A person who is already covered stays covered while scrolling.

**Other people models considered and ruled out (2026-10-18):**

| Model | What it is | Why not |
|---|---|---|
| MediaPipe SelfieSegmenter / SelfieMulticlass [50] | Google's phone segmenters, already in LiteRT format | Built to "segment the portrait of a person" (video calls, background effects); input only 256 × 256 px (144 × 256 landscape). A phone screen shrunk to 256 px makes a 96 px person about 10 px tall, so medium and small people (v4, v5) would be lost. |
| MediaPipe DeepLab-v3 [50] | General segmenter with a "person" class, 257 × 257 px | Same low input size; one mask for all people, so no per-person confidence |
| MobileSAM [51], EdgeSAM [52] | Fast, distilled versions of SAM | Need a **prompt** (a point or a box) for each object; they cannot find people by themselves, so they would still need a detector such as YOLO in front |
| FastSAM [53] | "Segment everything" with a CNN instance-segmentation model, then prompting | Finds all objects, not people; the underlying model is a YOLO-style segmenter anyway, so our YOLO26n-seg trained on people is the direct choice |

The SAM family stays useful **off the phone**, for labelling training pictures (SAM 3 with the text prompt "person", v5).

---

## 5. "Hide first" on Android: what is possible

| | Android 14+ (option B) | Android 13 and older (option C) |
|---|---|---|
| New content covered before it is checked? | **Yes**, after the event arrives | **No**. The cover would block our own capture. |
| Gap where unchecked content can show | Event delay plus one overlay redraw. **Not measured.** Likely a few frames. | About **one check** (≈ 300 ms today on CPU) plus the capture delay |
| Time content stays covered while checked | ≤ 333 ms (screenshot limit) + one check (≈ 300 ms) ≈ **0.3–0.7 s** | none (shown, then covered) |

This is a real trade-off for the user:
- **Strict** (B): almost nothing slips through. But every scroll covers new content for up to about half a second.
- **Fast** (C): no waiting. But new people can show for about a third of a second before they are covered.

`ponytail:` build B only (it matches the project's promise). C is dropped for now (2026-10-18): no Android 13 support; reconsider only if waiting feels too slow in testing.

**Scrolling and video:** during a fast scroll or a video, B covers the changed area until the next picture (max 3/s). In practice, a playing video stays mostly covered with a strict setting. Video gets its own stage, **v6** (roadmap): tracking between checks, screen capture during video only, or strict mode.

---

## 6. Speed budget on the phone

| Step | Today | Note |
|---|---|---|
| Window picture | max 3/s (333 ms gap) [5] | Android limit, not our code |
| Model, full screen, **GPU** (Mali-G52), 640 px | **~205 ms**, ~180 MB peak, ~4 s start-up | Measured 2026-10-07, same for fp32 / fp16 / dynamic-range |
| Model, CPU, 2 fast cores with fp16 math, 640 px | **277 ms**, 87 MB | Best CPU setting |
| Model, CPU fp32, 4 threads, 640 px | 295 ms cool (35 °C) → 388 ms warm (41 °C) | Heat slows the CPU by up to ~30% |
| Model, NNAPI | ≈ 1 CPU thread (761–1187 ms) | No help on this phone |
| Model at 480 px | GPU ~121 ms, CPU drq 122 ms | Fast, but loses a lot of accuracy, and the GPU needs ~52 s and ~470 MB to start |
| 3 tiles (for small people) | ≈ 3 × 205 ms ≈ 0.6 s on the GPU | Too slow for every change |

**Go / no-go (measured 2026-10-07):** at 640 px no setting reaches **150 ms** per full screen; only 480 px does, and it loses too much accuracy. So **640 stays, the GPU is the main path, and tiles (v4) are used only where the screen changed**, not on every full screen. Details: [`p0-results-android-v1.md`](p0-results-android-v1.md) §2.

---

## 7. Accuracy (summary)

The same model family as on Linux. On fake phone screens (1080 × 2340), with the threshold set to "hide when unsure" (0.1):

| Layout | Pass | Small people hidden | Medium | Large |
|---|---|---|---|---|
| Feed (Instagram home style) | whole screen | 24% | 71% | 85% |
| Feed | 3 tiles | 52% | 87% | 92% |
| Grid (Explore / search tab) | whole screen | 26% | 60% | 87% |
| Grid | 3 tiles | 54% | 87% | 95% |

Big people are fine. Small people are the open problem, like on Linux. Training on real phone screenshots (v5) is the main fix. More detail, including a check of the actual phone model file, is in [`p0-results-android-v1.md`](p0-results-android-v1.md).

---

## 8. Android and Xiaomi limits

| Limit | Effect | What we do |
|---|---|---|
| **Secure windows** (`FLAG_SECURE`: banking, Netflix and other video apps with DRM) | The window picture fails with a "secure window" error [4]. Screen capture shows black. | We cannot check pictures there; screen **text is still filtered** (it comes from the accessibility tree, not the picture). Banking apps rarely show people, but **streaming apps do**, so this is a real limit for video apps: state it in the report. Optional per-app "always cover" switch (covers the whole window). Corrected 2026-10-18: the earlier "most never show people" was wrong for streaming apps. |
| **Accessibility policy on Google Play** | Apps that are not accessibility tools need a declaration form and a clear in-app disclosure [7] | For the graduation project: install from an APK file. Still show a clear consent screen, since the service sees the whole screen. |
| **Xiaomi battery saver / autostart** | MIUI/HyperOS may stop background services | Setup screen asks the user to allow Autostart and set battery to "No restrictions" |
| **Android version** | Window picture needs Android 14 | The Redmi 12 runs Android 15. Older phones are not supported for now. |
| **Accessibility service turned off by the system** | The filter silently stops | Show a notification while the filter is running. If the service stops, the user sees the notification disappear. |

---

## 9. Prior work: HaramBlur (browser extension and Android app)

**"HaramBlur" already exists, in two forms.** The report must cite both. Our old working name was too close to it and was dropped on 2026-10-18 (issue C12).

| | Browser extension [8] | Android app [19] |
|---|---|---|
| Since / last update | v0.2.6 in the public repo; **no code pushed since Aug 2024**, while the store versions keep updating | Released 17 Nov 2025, v2.0.5 updated 1 Sep 2026 |
| Users | Chrome and Firefox stores; 2 083 GitHub stars | **~700 000 installs**, 4.6★ from 14 667 ratings |
| Price | Free (iOS version is paid, per issue #211) | Free with **in-app purchases ($3.99–$34.99)** |
| How | A script inside each web page | **Accessibility service**, on-device AI |
| Hides | Images and videos (whole image blurred) | Images, and videos frame by frame |
| Where | Websites | "Popular social media and browsing apps" (its own words, so likely a fixed list of apps) |
| Text / bad words | **None** | **None** |
| Code | Open source, **AGPL-3.0** | Closed (the store page does not link code) |

### Known problems (checked 2026-10-06)

Sources: **our own use** of the Android app; **163 GitHub issues** on the extension repo (90 still open) [8]; **364 recent Play Store reviews** of the Android app (June–October 2026, English and Arabic, fetched with `google-play-scraper`; 44 of them have 1–3 stars) [19]. Counts below are from keyword searches, so they are rough.

| Problem | Evidence | How our design answers it |
|---|---|---|
| **Asks for permission again and again** | Our own use. A review: settings get mixed up and it asks for permissions again. One review says it needs Android 15. | This pattern fits **screen capture (MediaProjection)**, which needs a new consent prompt every session on Android 14+ (§2) — likely their method, not confirmed. Our v1 needs **no screen capture at all**. v3+ uses the accessibility window picture: allowed **once** in settings. |
| **Content shows before the blur** (the most common complaint) | ~20 reviews: "takes 1–2 seconds", "slow", "doesn't blur instantly", including many 5★ reviews. GitHub #190: images and videos visible **1–3 s** before detection in the app. Extension: #106, #111, #168; its "blurry start" lifts after 7 s anyway. | **Hide first**: changed content stays covered until checked, and the cover never lifts by itself (FR-14). Text is checked in under 1 ms. |
| **Feels heavy** | Our own use. Reviews: "slow", "lag". Extension: 2–5 GB RAM (#130, #133), 100% CPU (#153), VRAM leak (#192), "makes the whole device slow" (#220). | **Event-driven**: no work while the screen is still. v1 runs no AI model. Memory targets: v1 < 50 MB, with people model: target < 250 MB, hard limit ≤ 500 MB (NFR-9). |
| **Misses images** | Our own use. Reviews: far-away people, anime, drawings, manga, small pop-ups. GitHub: small images and thumbnails (#124, #213), CSS background images (#25, #159), lazy-loaded images (#219), women with headphones (#171), manga (#204). | Every visible image is checked (not only `<img>` tags), because we look at the window picture. Small and medium people are planned stages (v4, v5) with measured accuracy targets. |
| **Blurs the wrong thing** | ~15 reviews: blurs men instead of women, a man's lecture, a flower drawing; the whole video when one person moves. GitHub #175 (a man's hand), #72. | **No gender guess**: we hide all people (§9, "What is different"). We cover the **person's mask**, not the whole image or video. |
| **Cover in the wrong place / not following** | Reviews: the blur stays fixed in one place and does not track the video; it stays on screen after leaving the video; "a blurred picture next to the real picture". GitHub #212 (offset cover). | Covers move with scrolling (FR-3), and are re-placed after every check. |
| **Light blur still shows details** | A review: the blur is light and shows details. | **Solid block or strong pixelation**, never a light blur (FR-13). |
| **Only some apps** | Reviews ask for TikTok (5+), Facebook; one says it "only works in the internal browser". | Every app that shares its text (v1) or can be pictured (v3+). |
| **Closed and paid** | The public repo has no code since Aug 2024; issues #148, #188, #189, #217 ask whether it is still open source; ~8 reviews complain about paid features. | Graduation project: our code and documents stay open. |
| **No text filtering** | Neither product filters words. | v1 is a bad-language text filter. |

### How the browser extension works (from its code)

We read the extension's code for ideas. **We do not copy its code.**

| Part | What it does |
|---|---|
| Where | Inside Chrome or Firefox only. A script in every web page watches for new `<img>` and `<video>` elements. |
| What it checks | Images ≥ 32 px. **nsfwjs** sorts the whole image (224 px) into drawing / hentai / neutral / porn / sexy. **Human** finds faces (BlazeFace, at most 2) and guesses gender and age. It blurs if it finds a face of the chosen gender (default: women) over age 20. |
| Cover | Blurs the **whole image** (CSS blur 20 px plus grayscale), not just the person |
| "Blurry start" | Optional, **off by default**. New images start blurred and are unblurred after the check. **After 7 s they unblur anyway**, even if the check did not finish. |
| Video | Up to 25 checks per second, one at a time. Frames older than 0.5 s are dropped. Blur after **1** positive frame, unblur after **3** clean frames. |
| Saving work | If a frame barely changed from the last one, it reuses the last answer (for up to 4 s or 99 frames). |
| Settings | On/off, strictness slider (video is 25% less strict), blur amount, grayscale, hover to unblur, per-site whitelist |
| Text | **None.** It does not filter bad language. |

### What we take as ideas

| Idea | Where it goes in our project |
|---|---|
| Blur fast, unblur slow (1 positive vs 3 clean frames) | Cover tracking in v3–v5 (and for text that changes) |
| Skip the model if the screen barely changed | Saves battery in v3–v5 |
| Strictness slider | Settings: one slider for people, plus category switches for text |
| Whitelist | Per-app skip list (FR-4) |
| Start covered, then check | We already do this for people ("hide first"), but **without** the 7 s timeout. Our cover never lifts on its own. |

### What is different in our project

- **v1 hides bad-language text**, which neither HaramBlur product does at all
- **Every app** that shares its text or can be pictured, not a list of popular apps
- **Covers only the person** (mask), not the whole image
- **Hide first without a timeout.** Unchecked content stays covered.
- **All people, no gender guess.** Guessing gender from a face fails for people seen from behind, far away, or partly visible, and a wrong guess means exposure (Linux investigation §9).

---

## 10. Next steps (in release order)

| Step | What | Answers | Size |
|---|---|---|---|
| **v1-a: app skeleton** | Accessibility service, overlay, settings screen, notification, consent screen. Read the screen text and print it to the log. | Which apps give us their text? | ~1 week |
| **v1-b: text filter** | Normalization, matcher, word boxes, cover (word / message), covers follow scrolling | The gap before the cover. Do word boxes work in Chrome and in big social apps? | ~1–2 weeks |
| **v1-c: word lists and test** | Team builds the Arabic list (start: LDNOOBW V2 + Attia's categories, §3.3) and reviews the English list. Test on OSACT tweets and clean text. | Words hidden, false covers (§3.4) | ~1 week, can run in parallel |
| **v1.1: own text model** | P0c (phone test of all candidates, then quality test), then data + teacher labels + training per language pack + comparison (§3.5) | Is our small model better than the word list and the baselines, fast enough on the phone? | ~4–5 weeks, in parallel with v3 |
| ~~P0b: finish the phone speed test~~ | Done 2026-10-07 ([`p0-results-android-v1.md`](p0-results-android-v1.md)) | GPU ~205 ms at 640 px; nothing reaches 150 ms at 640 | done |
| P0d: OCR phone test | PaddleOCR PP-OCRv5 Arabic and English mobile models on the Redmi 12, CPU and GPU | Speed, RAM, accuracy on memes and thumbnails | days, **before v2** |
| v2: text inside images | Window picture, OCR, same text filter, cover words inside images | Waiting time, words hidden in images | ~3–4 weeks |
| v3: big people | Window picture, LiteRT model + NMS, mask cover, hide first | End-to-end delay, battery, big-people accuracy on real screenshots | ~2 weeks |
| v4: medium people | Tiles, plus the faster model setup from P0b | Medium-people accuracy versus speed | ~1–2 weeks |
| v5: small people | Real phone screenshots, SAM 3 labels, fine-tune | Small-people accuracy | weeks |
| v6: video | Compare tracking, screen capture during video, strict mode | People visible per second of video | ~3 weeks |

Linux tests stay valid for the model work (v3–v5). The Linux plugin is paused.

---

## 11. Useful resources (found 2026-10-06)

### For v1 (text)

| Resource | Use | License |
|---|---|---|
| LDNOOBW V2 word lists [14] | Start of the Arabic list (348 Arabic-script entries); Arabizi later | CC0 |
| Attia Arabic offensive lexicon [15] | Categories and extra terms for the Arabic list | No license: cite, ask before copying |
| LDNOOBW English list [11] | English list (review it first) | CC-BY-4.0 |
| HAYAA-student [18] | Optional second check: 9.6 MB Arabic toxicity model, ONNX / TFLite | Research use only |
| Apache Lucene `ArabicNormalizer` [20] | The cleaning rules we need (alef forms, ة→ه, ى→ي, tashkeel, tatweel). About 15 lines: **rewrite them**, do not add Lucene. | Apache-2.0 |
| Aho-Corasick for Java [21] | Fast lookup of many phrases in one pass. A plain set of words is enough for single words, so add this only if phrase lookup is slow. | Apache-2.0 |
| OSACT 2020 data [12], Mubarak 2017 data [17] | Test sets of real Arabic tweets | Research use |
| Arabic offensive-language preprocessing papers [22] | Tested cleaning rules (letter forms, cut repeated letters to two) | — |
| Arabizi offensive-language detection (2023) [23] | When Arabizi is added after v1 | — |

### For building the app

| Resource | Use | License |
|---|---|---|
| Google codelab "Developing an Accessibility Service for Android" [24] | Starting point for v1-a: about 200 lines in 4 files | not checked |
| ChiaraSelect2Speak [25] | Example of an accessibility service with overlay, screenshots and OCR | GPL-3.0: read, do not copy |

### For later

| Resource | Use |
|---|---|
| PaddleOCR PP-OCRv5 Arabic mobile [16] | Text inside images and videos. About 7.6 MB (ONNX) or 8 MB (MNN). Ente Photos already runs PaddleOCR on Android [26]. The team has PaddleOCR experience. |
| SafeGaze / Kahf Halal Browser [27] | Another competitor (browser only). Users say it blurs every photo of a person. |

---

## Sources

1. Redmi 12 specs: [GSMArena](https://m.gsmarena.com/xiaomi_redmi_12-ampp-12328.php), [mi.com](https://www.mi.com/global/redmi-12/specs)
2. MediaProjection, consent per session on Android 14: [developer.android.com/media/grow/media-projection](https://developer.android.com/media/grow/media-projection)
3. Untrusted-touch rules and the 80% opacity cap for see-through app overlays: [AOSP commit a451d5b](https://android.googlesource.com/platform/frameworks/base/+/a451d5bae2e2), [Android tapjacking guide](https://developer.android.com/topic/security/risks/tapjacking)
4. `takeScreenshotOfWindow`, accessibility overlays (API 34): [AccessibilityService reference](https://developer.android.com/reference/android/accessibilityservice/AccessibilityService), [API 34 diff](https://developer.android.com/sdk/api_diff/34/changes/android.accessibilityservice.AccessibilityService)
5. Screenshot rate limit, `ACCESSIBILITY_TAKE_SCREENSHOT_REQUEST_INTERVAL_TIMES_MS`: 1000 ms on Android 11, **333 ms** on Android 13, 14 and current. Read from AOSP source, which applies it per window: [AccessibilityService.java](https://android.googlesource.com/platform/frameworks/base/+/master/core/java/android/accessibilityservice/AccessibilityService.java), [AbstractAccessibilityServiceConnection.java](https://android.googlesource.com/platform/frameworks/base/+/master/services/accessibility/java/com/android/server/accessibility/AbstractAccessibilityServiceConnection.java)
6. Trying to hide an overlay from screen capture on a MediaTek phone: [LSFG-Android issue #12](https://github.com/FrankBarretta/LSFG-Android/issues/12)
7. Google Play accessibility policy: [support.google.com/googleplay/android-developer/answer/10964491](https://support.google.com/googleplay/android-developer/answer/10964491)
8. HaramBlur browser extension: [github.com/alganzory/HaramBlur](https://github.com/alganzory/HaramBlur) (code read at commit f47000e, July 2024; [issues](https://github.com/alganzory/HaramBlur/issues) read 2026-10-06)
9. Character boxes for text, `EXTRA_DATA_TEXT_CHARACTER_LOCATION_KEY` and `refreshWithExtraData` (API 26): [API 26 diff](https://developer.android.com/sdk/api_diff/26/changes/android.view.accessibility.AccessibilityNodeInfo), [AccessibilityNodeInfo reference](https://developer.android.com/reference/android/view/accessibility/AccessibilityNodeInfo)
10. ML Kit text recognition v2 languages (Latin, Chinese, Devanagari, Japanese, Korean; no Arabic): [developers.google.com/ml-kit/vision/text-recognition/v2/languages](https://developers.google.com/ml-kit/vision/text-recognition/v2/languages)
11. LDNOOBW word lists, CC-BY-4.0: [github.com/LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words](https://github.com/LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words)
12. OSACT 2020 Arabic offensive-language shared task: [aclanthology.org/2020.osact-1.7](https://aclanthology.org/2020.osact-1.7)
13. Chrome on Android handles `EXTRA_DATA_TEXT_CHARACTER_LOCATION_KEY`: [WebContentsAccessibilityImpl.java](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/content/public/android/java/src/org/chromium/content/browser/accessibility/WebContentsAccessibilityImpl.java)
14. LDNOOBW V2, CC0 (Arabic: 1 284 entries, counted 2026-10-06): [github.com/LDNOOBWV2/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words_V2](https://github.com/LDNOOBWV2/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words_V2)
15. Attia, M. (2025), Arabic offensive, vulgar, slur and profane words: [github.com/mohammedattia/arabic-offensive-words](https://github.com/mohammedattia/arabic-offensive-words)
16. PaddleOCR on-device deployment: [paddleocr.ai](https://www.paddleocr.ai/v3.3.1/en/version3.x/deployment/on_device_deployment.html); Arabic PP-OCRv5 mobile exports: [ONNX](https://huggingface.co/mxaln/docscanner-ocr), [MNN](https://huggingface.co/playtranslate/ocr-models)
17. Mubarak, Darwish, Magdy (2017), Abusive Language Detection on Arabic Social Media: [aclanthology.org/W17-3008](https://aclanthology.org/W17-3008/)
18. HAYAA-student (int8): [huggingface.co/MahmoudMabrok/HAYAA-student-int8](https://huggingface.co/MahmoudMabrok/HAYAA-student-int8)
19. HaramBlur Android app: [Google Play, com.haramblur](https://play.google.com/store/apps/details?id=com.haramblur&hl=en_US) (metadata and 364 reviews fetched 2026-10-06 with [google-play-scraper](https://pypi.org/project/google-play-scraper/))
20. Lucene ArabicNormalizer: [lucene.apache.org](https://lucene.apache.org/core/8_5_1/analyzers-common/org/apache/lucene/analysis/ar/ArabicNormalizer.html)
21. Aho-Corasick for Java: [github.com/robert-bor/aho-corasick](https://github.com/robert-bor/aho-corasick)
22. OSACT4 preprocessing approach: [arxiv.org/abs/2005.07297](https://arxiv.org/pdf/2005.07297); ML ensemble approach: [arxiv.org/abs/2005.08946](https://arxiv.org/pdf/2005.08946)
23. Offensive Language Detection in Arabizi (2023): [ACL Anthology 2023.arabicnlp-1.36](https://preview.aclanthology.org/credits/2023.arabicnlp-1.36)
24. Google codelab: [Developing an Accessibility Service for Android](https://codelabs.developers.google.com/codelabs/developing-android-a11y-service)
25. ChiaraSelect2Speak: [github.com/HackaHealth-Geneva/ChiaraSelect2Speak](https://github.com/HackaHealth-Geneva/ChiaraSelect2Speak)
26. Ente, open-source Android OCR: [ente.com/blog/ocr](https://ente.com/blog/ocr/)
27. SafeGaze browser extension: [Chrome Web Store](https://chrome.google.com/webstore/detail/safegaze-browser-extensio/aaddkkmpkpcnchdggomfaehpagbekalb)
28. TypeSafe AI, Jev ("System One" decision model, Sep 2026): [StartupHub article](https://startuphub.ai/ai-news/artificial-intelligence/2026/typesafe-jev-model-kills-chat), [eesel.ai explainer](https://www.eesel.ai/fr/blog/typesafe-jev)
29. Jev 1.13 on OpenRouter: [openrouter.ai/typesafe/jev-1.13](https://openrouter.ai/typesafe/jev-1.13/api)
30. Open-source Jev alternatives (Laya, Von, Kev, NanoJev, ...): [DataCamp](https://www.datacamp.com/blog/top-open-source-jev-alternatives); GLiNER2.5-Decide: [huggingface.co/fastino/gliner2.5-decide](https://huggingface.co/fastino/gliner2.5-decide)
31. Laya multilingual: [huggingface.co/convaiinnovations/laya-multilingual](https://huggingface.co/convaiinnovations/laya-multilingual); LiteRT build with phone timings: [huggingface.co/litert-community/Laya-Multilingual-LiteRT](https://huggingface.co/litert-community/Laya-Multilingual-LiteRT)
32. Qwen3Guard Technical Report: [arXiv 2510.14276](https://arxiv.org/abs/2510.14276); [Qwen3Guard-Stream-0.6B](https://huggingface.co/Qwen/Qwen3Guard-Stream-0.6B)
33. mmBERT: [arXiv 2509.06888](https://arxiv.org/abs/2509.06888); [huggingface.co/jhu-clsp/mmBERT-small](https://huggingface.co/jhu-clsp/mmBERT-small)
34. ArabicDialectSafety (2026): [arXiv 2608.01291](https://arxiv.org/abs/2608.01291)
35. ArGuard shared task (2026): [arXiv 2609.29349](https://arxiv.org/abs/2609.29349)
36. FanarGuard: [arXiv 2511.18852](https://arxiv.org/abs/2511.18852)
37. multilingual-toxicity-small (mmBERT-small, Apache-2.0): [huggingface.co/Horizon-Labs/multilingual-toxicity-small](https://huggingface.co/Horizon-Labs/multilingual-toxicity-small)
38. SemEval-2021 Task 5, Toxic Spans Detection: [aclanthology.org/2021.semeval-1.6](https://aclanthology.org/2021.semeval-1.6/)
39. ARBERT & MARBERT: [aclanthology.org/2021.acl-long.551](https://aclanthology.org/2021.acl-long.551/)
40. CAMeLBERT (Inoue et al. 2021): [aclanthology.org/2021.wanlp-1.10](https://aclanthology.org/2021.wanlp-1.10/)
41. Ushio, Zhou, Camacho-Collados, Efficient Multilingual Language Model Compression through Vocabulary Trimming, Findings of EMNLP 2023: [aclanthology.org/2023.findings-emnlp.981](https://aclanthology.org/2023.findings-emnlp.981/)
42. Hassan et al., ALT Submission for OSACT Shared Task on Offensive Language Detection (SVM + DNN, 1st in Subtask A, F1 90.51%), OSACT 2020: [aclanthology.org/2020.osact-1.9](https://aclanthology.org/2020.osact-1.9/)
43. Model2Vec (MinishLab), static embeddings distilled from sentence models: [github.com/MinishLab/model2vec](https://github.com/MinishLab/model2vec)
44. potion-multilingual-128M (MIT): [huggingface.co/minishlab/potion-multilingual-128M](https://huggingface.co/minishlab/potion-multilingual-128M); Zarra, Arabic Model2Vec model (MIT): [huggingface.co/NAMAA-Space/zarra](https://huggingface.co/NAMAA-Space/zarra)
45. EmbeddingGemma: [Google Developers Blog](https://developers.googleblog.com/en/introducing-embeddinggemma/), [arXiv 2509.20354](https://arxiv.org/abs/2509.20354)
46. Gemma 3 270M: [Google Developers Blog](https://developers.googleblog.com/introducing-gemma-3-270m/)
47. Multilingual E5 Text Embeddings, technical report: [arXiv 2402.05672](https://arxiv.org/abs/2402.05672); [intfloat/multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small)
48. TFLite memory-mapped model files: [Google Developers Blog, Streamlining LLM inference at the edge with TFLite](https://developers.googleblog.com/en/streamlining-llm-inference-at-the-edge-with-tflite/)
49. Hugging Face model pages, checked 2026-10-07: [asafaya/bert-mini-arabic](https://huggingface.co/asafaya/bert-mini-arabic), [asafaya/bert-medium-arabic](https://huggingface.co/asafaya/bert-medium-arabic), [microsoft/Multilingual-MiniLM-L12-H384](https://huggingface.co/microsoft/Multilingual-MiniLM-L12-H384), [distilbert-base-multilingual-cased](https://huggingface.co/distilbert/distilbert-base-multilingual-cased), [aubmindlab/bert-base-arabertv02](https://huggingface.co/aubmindlab/bert-base-arabertv02), [FacebookAI/xlm-roberta-base](https://huggingface.co/FacebookAI/xlm-roberta-base), [microsoft/mdeberta-v3-base](https://huggingface.co/microsoft/mdeberta-v3-base), [Alibaba-NLP/gte-multilingual-base](https://huggingface.co/Alibaba-NLP/gte-multilingual-base), [LiquidAI/LFM2-350M](https://huggingface.co/LiquidAI/LFM2-350M), [wfzyx/von-1.0](https://huggingface.co/wfzyx/von-1.0), [HuggingFaceTB/SmolLM2-135M](https://huggingface.co/HuggingFaceTB/SmolLM2-135M)
50. MediaPipe Image Segmenter, supported models (SelfieSegmenter, SelfieMulticlass, DeepLab-v3), checked 2026-10-18: [developers.google.com](https://developers.google.com/edge/mediapipe/solutions/vision/image_segmenter)
51. C. Zhang *et al.*, "Faster Segment Anything: Towards lightweight SAM for mobile applications" (MobileSAM): [arXiv 2306.14289](https://arxiv.org/abs/2306.14289)
52. C. Zhou *et al.*, "EdgeSAM: Prompt-in-the-loop distillation for on-device deployment of SAM": [arXiv 2312.06660](https://arxiv.org/abs/2312.06660)
53. X. Zhao *et al.*, "Fast Segment Anything" (FastSAM): [arXiv 2306.12156](https://arxiv.org/abs/2306.12156)
