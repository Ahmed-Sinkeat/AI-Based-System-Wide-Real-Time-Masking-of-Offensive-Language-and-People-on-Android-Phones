# AI-Based System-Wide Real-Time Masking of Offensive Language and People on Android Phones

**إخفاء الألفاظ السيئة وصور الأشخاص على مستوى النظام وفي الوقت الفعلي على هواتف أندرويد باستخدام الذكاء الاصطناعي**

Graduation project, Software Engineering. **Team:** Ahmed Mohammed Omer · Omer Abd Almonim · Momen Kamal

An Android app that hides offensive language and images of people on the phone screen, across the apps people use every day (limits: [SRS §5](docs/srs-en.html#scope)), using AI that runs on the phone itself. **Nothing leaves the phone:** the app has no internet permission.

---

## Release plan

| Version | Hides | Status |
|---|---|---|
| **v1** | Bad words in on-screen text (Arabic + English): a word list, plus our own small text model for context-dependent insults (trained from large "teacher" models) | Next: app skeleton (v1-a) |
| **v2** | Bad words in text **inside images** (memes, thumbnails, subtitles), with on-phone OCR | Planned |
| **v3** | Big people (taller than ~96 px on screen) | Model tested: 85–95% hidden |
| **v4** | Medium people (~32–96 px), checking the screen in tiles | Model tested: 87–89% with tiles |
| **v5** *(bonus)* | Small people (under ~32 px), with our own fine-tuned model | The hard part: 51–54% with tiles today |
| **v6** *(after graduation)* | People in videos while they play | Future work |

**Graduation scope: v1 to v4.** v5 is a bonus if time allows; v6 comes after graduation.

Plan by week: [`docs/roadmap.md`](docs/roadmap.md). Deadline: about mid-April 2027.

## Key decisions

| Decision | Why |
|---|---|
| **Android**, not PC | It is where people scroll. Phone results are good enough for text and big people. Small people are hard on any hardware. |
| **On the phone**, not the cloud | Privacy (no screen pictures sent anywhere), works without internet, no mobile data cost, no server bill. Big models are used only while **training**, on a laptop or Colab. |
| **Window picture** (accessibility service), not screen casting | Android allows it once in settings, with no prompt each session. The picture does not include our own covers, so we can cover first and check under the cover. The model handles ~5 pictures per second anyway, so casting's 60 frames per second would be wasted. |
| **Android 14+** for picture features | Needed for the window picture. Older phones are not supported for now. |
| **Hide the whole person**, no gender guess | A wrong guess shows a person. Hiding too much is acceptable; showing too much is not. |

Details and evidence: [`docs/asbuild.md`](docs/asbuild.md) (every decision, dated) and [`docs/README.md`](docs/README.md) (all documents).

## Project rule

**Every decision, change, or obstacle gets a dated entry in [`docs/asbuild.md`](docs/asbuild.md)** (what, why, alternatives, what got in the way, evidence). Open problems go in [`docs/issue.md`](docs/issue.md).

## Where things are

| Folder | What |
|---|---|
| [`docs/`](docs/README.md) | All documents: start at [`docs/README.md`](docs/README.md) |
| [`wordlists/`](wordlists/README.md) | Combined Arabic bad-word list (1 906 terms from 7 sources) and the script that builds it |
| `bench/` | Model tests on the laptop and the phone (Python) |
| `app/` | The Android app (not started yet) |

## Getting the data (not in git)

These are large or rebuildable, so they are not stored in the repository:

| Path | How to get it |
|---|---|
| `.venv/` | Python 3.12 virtual environment: `openvino nncf ultralytics rfdetr pycocotools onnxruntime ai-edge-litert onnx2tf tensorflow` |
| `bench/data/` | COCO val2017 images and `annotations/instances_val2017.json` |
| `bench/datasets/coco128-seg` | Downloaded automatically by Ultralytics |
| `bench/*.pt`, `bench/*.onnx`, `bench/models*/` | Downloaded or exported by `bench/export.py` and `bench/export_tflite.py` |
| `bench/neo/` | Intel GPU compute runtime unpacked from Arch packages (see `bench/env.sh`; paths in it are machine-specific) |
| `bench/phone_tools/benchmark_model` | LiteRT `benchmark_model` binary for Android arm64 |
