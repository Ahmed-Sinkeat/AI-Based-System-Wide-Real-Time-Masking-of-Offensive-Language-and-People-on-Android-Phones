# AI-Based System-Wide Real-Time Masking of Offensive Language and People on Android Phones

**إخفاء الألفاظ السيئة وصور الأشخاص على مستوى النظام وفي الوقت الفعلي على هواتف أندرويد باستخدام الذكاء الاصطناعي**

Graduation project, Software Engineering. Working name: **HaramBlurr**.

An Android app that hides offensive language and images of people on the phone screen, in every app, using AI that runs on the phone itself. Nothing leaves the phone.

**Release order:** v1 bad-language text (Arabic + English) → v1.1 our own small text model → v2 big people → v3 medium people → v4 small people.

**Team:** Ahmed Mohammed Omer · Omer Abd Almonim · Momen Kamal

---

## Project rule

**Every decision, change, or obstacle gets a dated entry in [`docs/asbuild.md`](docs/asbuild.md)** (what, why, alternatives, what got in the way, evidence). Open problems go in [`docs/issue.md`](docs/issue.md).

---

## Where things are

| Folder | What |
|---|---|
| [`docs/`](docs/README.md) | All documents: start at [`docs/README.md`](docs/README.md) (design, requirements, roadmap, research methods, results, as-built log, issues) |
| [`wordlists/`](wordlists/README.md) | Combined Arabic bad-word list and the script that builds it |
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
