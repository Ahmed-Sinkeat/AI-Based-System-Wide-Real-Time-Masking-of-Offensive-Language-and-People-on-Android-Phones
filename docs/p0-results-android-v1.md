# HaramBlurr — P0 Results on the Phone (Android v1)

Date: 2026-10-03 (phone runs) and 2026-10-06 (checks and fixes) · Phone: Xiaomi Redmi 12 (Helio G88) · Laptop for offline runs: i5-1135G7
Scope: the **people** model, used in v2–v4 ([`investigation-android-v1.md`](investigation-android-v1.md) §10). Offline tests only. No app code exists yet.

> **v1 hides bad-language text and needs no AI model**, so nothing here blocks v1. These results matter from v2 (big people) onward. Text tests are planned in the investigation §3.4.

Raw data: `bench/results/phone/`, `bench/results/phone_tflite_*/`, `bench/results/phone_latency.csv`.

---

## 1. Bottom line

| Question | Answer |
|---|---|
| How fast is the model on the Redmi 12? | **295 ms** per full-screen check (fp32, CPU, 4 threads). About **3 checks per second**. The faster options were **not measured**: the test stopped after 2 of about 12 runs. |
| Is the phone model file correct? | **fp32: yes.** It finds the same people as the laptop model. **INT8: no, it was broken.** It found **nobody** (0 of 448 people), so it was moved to `models_tflite/broken/` (§4). |
| Does it hide people on phone-like screens? | **Large people: yes** (85–95%). **Small people: no.** One pass hides 24–27% of them. Three tiles hide 52–54%. |
| What next? | v1 (text) does not need this model, so the app work can start now. Re-run the phone speed test (§5) **before v2**. |

---

## 2. Speed on the Redmi 12 (LiteRT `benchmark_model` over adb)

| Model | Input | Run on | avg ms | p95 ms | Peak memory | Status |
|---|---|---|---|---|---|---|
| yolo26n-seg fp32 | 640 | CPU, 4 threads | **295** | 310 | 98 MB | measured |
| yolo26n-seg fp32 | 640 | CPU, 2 threads | 463 | 481 | 98 MB | measured |
| yolo26n-seg fp32 | 640 | CPU 1 thread, GPU, NNAPI, CPU forced-fp16 | — | — | — | **not run** (test stopped) |
| yolo26n-seg INT8 | 640 | all | — | — | — | **not run**, and the file was broken anyway |
| yolo26n-seg (any) | 480 / 320 | all | — | — | — | **not exported** (export stopped too) |

- **Why it stopped is unknown.** The log ends after the second run, with no error. The likely causes are an unplugged phone or a closed terminal. The script only saved its results file **at the very end**, so nothing was written. **Fixed:** `bench/bench_phone.py` now saves after every run. The 2 finished rows were recovered from the log into `results/phone_latency.csv`.
- 4 threads is only 1.6× faster than 2 threads. The Helio G88 has only 2 fast cores, so threads 3 and 4 run on slow cores.
- The phone has no fan. The script waits 20 s between runs. Battery temperature was 35–36 °C.

---

## 3. Accuracy on phone-like screens

`bench/phone.py` builds fake phone screens (1080 × 2340) from COCO photos in two layouts:
- **feed**: full-width posts, like the Instagram or Facebook home page (60 screens, 473 people)
- **grid**: 3 columns of squares, like the Explore or search tab (60 screens, 3 670 people)

"Hidden" means at least 90% of the person is under the cover. Size buckets: small < 32², medium < 96², large ≥ 96² screen pixels. Threshold 0.1 means "hide when unsure".

### 3.1 Threshold 0.1, cover = mask made a bit bigger

| Model | Layout | Pass | Small | Medium | Large | Pixels covered | Over-cover |
|---|---|---|---|---|---|---|---|
| laptop OpenVINO INT8 (yolo26n) | feed | whole screen | 23.7 | 70.9 | 85.3 | 94.1 | 23.7 |
| | feed | 3 tiles | **51.8** | 87.4 | 92.2 | 90.8 | 25.7 |
| | grid | whole screen | 25.6 | 59.6 | 87.4 | 87.4 | 42.6 |
| | grid | 3 tiles | **54.0** | 86.8 | 94.8 | 95.4 | 39.6 |
| **phone file, fp32** (`yolo26n-seg_640_fp32.tflite`) | feed | whole screen | 23.7 | 75.6 | 88.4 | 95.8 | 23.4 |
| | feed | 3 tiles | **53.5** | 89.0 | 91.4 | 91.1 | 25.3 |
| | grid | whole screen | 27.4 | 63.6 | 89.5 | 88.8 | 42.9 |
| | grid | 3 tiles | **54.3** | 88.1 | 94.9 | 95.6 | 39.4 |
| phone file, dynamic-range (`_drq`) | feed | whole screen | 19.3 | 72.4 | 87.5 | 95.6 | 23.0 |
| | feed | 3 tiles | **50.9** | 87.4 | 92.7 | 91.2 | 25.7 |
| | grid | whole screen | 26.0 | 61.1 | 88.0 | 88.1 | 42.9 |
| | grid | 3 tiles | **53.8** | 86.9 | 95.3 | 95.5 | 39.9 |

### 3.2 What this means

- **The phone fp32 file works.** It matches the laptop model and is 1–4 points better (fp32 vs INT8).
- **The dynamic-range file (3 MB, for the phone CPU) is almost as good as fp32**: within about 2 points, except small people in the feed with one pass (19.3 vs 23.7). With tiles the gap is under 3 points. If it is faster on the phone, it is the CPU choice.
- **Small people are the problem, as on Linux.** Half of the missed people are under about **40 px tall** on screen (38–44 px median, about 2.5 mm on a ~400 ppi screen). The model input is 640 px for a 2340 px tall screen, so the model sees them 3.7× smaller still: about 10 px. See `results/phone/missed_people_sheet.jpg`.
- **3 tiles roughly double small-person recall.** But they cost 3 checks, about 0.9 s on the CPU today.
- **Over-cover is high in the grid layout (≈40%)**, because small people get a cover that is big compared to them. That is acceptable: hiding too much is fine, showing a person is not.
- These are COCO photos on fake screens. Real app screenshots are still untested (v4).

Pictures of what the user would see: `results/phone/feed_*.jpg`, `grid_*.jpg` (green = hidden, orange = partly, red = missed).

---

## 4. Things that broke (and what they mean)

| Finding | Evidence | Consequence |
|---|---|---|
| **Full-INT8 phone model finds nobody** | Class scores are all 0.0000. 0 of 448 strong person detections kept vs fp32. Accuracy test: 0% hidden everywhere (`results/phone_tflite_int8_broken/`). | Boxes (0–640) and scores (0–1) share one output tensor and one INT8 scale, so scores round to 0. The file was moved to `models_tflite/broken/`. Benchmarking it on the phone would have shown a fast model that does nothing. |
| Other variants of the same export are fine | Strong detections kept vs fp32: float16 446/448, dynamic-range 424/448, int8-with-int16-activations 435/448 | `export_tflite.py` now outputs **fp32, fp16 (for GPU) and drq (for CPU)**. Full INT8 would need boxes divided by the input size before export (as Ultralytics' own TFLite export does). Marked `ponytail:` in the script. |
| **Phone speed test stopped after 2 of ~12 runs**, with no results file | `results/bench_phone_640.log` ends after `cpu2`. `phone_latency.csv` missing. | `bench_phone.py` now saves after each run. Rows recovered. |
| **TFLite export stopped after the 640 model** | `results/export_tflite.log` ends at 640. The 480 folder has float files only. 320, yolo11n and yolo26s were never exported. | 480 fp32/fp16/drq copied into `models_tflite/`. Re-run `export_tflite.py` for the rest when needed. |
| `bench/yolo26n-seg.onnx` is the **480** export, not 640 | ONNX input 480 × 480 | Each export overwrites it. Do not use that file as "the 640 model". |
| Phone model needs its own NMS | Output is 116 × 8400 boxes (the export does not include the de-duplication step) | The app must do NMS (a few lines). Same decode as `bench/ov_seg.py`. |

---

## 5. To do before v2 (phone plugged in, about 1 evening)

```
cd bench && source env.sh
python bench_phone.py 640          # fp32, fp16, drq on CPU 1/2/4 threads, GPU, NNAPI
python bench_phone.py 480          # smaller input: faster, but small people get worse
```

Then also measure accuracy at 480 with `phone.py` / `phone_tflite.py`. Decision rule from the investigation: **one full-screen check must take ≤ about 150 ms**, otherwise tiles do not fit on this phone.

---

## Reproducing

| What | Command (in `bench/`, after `source env.sh`) |
|---|---|
| Phone-screen accuracy, laptop model | `python phone.py ov-yolo:models/yolo26n-seg_int8_openvino_model/yolo26n-seg.xml:GPU 60` |
| Phone-screen accuracy, phone file | `python phone_tflite.py fp32 60` (or `fp16`, `drq`) |
| Export phone files | `python export_tflite.py` |
| Phone speed (adb, phone plugged in) | `python bench_phone.py [name filter]` |
