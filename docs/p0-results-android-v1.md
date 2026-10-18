# P0 Results on the Phone (Android v1)

Date: 2026-10-03 (first phone runs), 2026-10-06 (checks and fixes), 2026-10-07 (full phone speed test, 480 px and fp16 accuracy, sustained CPU/GPU test) · Phone: Xiaomi Redmi 12 (Helio G88, Android 15, 8 GB) · Laptop for offline runs: i5-1135G7
Scope: the **people** model, used in v3–v5 ([`investigation-android-v1.md`](investigation-android-v1.md) §10). Offline tests only. No app code exists yet.

> **v1 hides bad-language text and needs no AI model**, so nothing here blocks v1. These results matter from v3 (big people) onward. Text tests are planned in the investigation §3.4.

Raw data: `bench/results/phone/`, `bench/results/phone_tflite_*/`, `bench/results/phone_latency.csv`, `bench/results/phone_sustained_2026-10-07.csv` and its `.log`.

---

## 1. Bottom line

| Question | Answer |
|---|---|
| How fast is the model on the Redmi 12? | **GPU: ~205 ms** per full-screen check at 640 px (about 5 per second). **CPU: 277 ms** at best (2 fast cores, fp16 math). NNAPI does not help. Warm phones are up to ~30% slower on the CPU (§2). |
| Is the phone model file correct? | **fp32: yes.** It finds the same people as the laptop model. **INT8: no, it was broken.** It found **nobody** (0 of 448 people), so it was moved to `models_tflite/broken/` (§4). |
| Does it hide people on phone-like screens? | **Large people: yes** (85–95%). **Small people: no.** One pass hides 24–27% of them. Three tiles hide 52–54%. **480 px is faster but loses a lot** (e.g. medium people in the grid 64% → 41%), so **640 stays**. fp16 is as accurate as fp32. |
| What next? | P0b is done. **The ≤ 150 ms rule for tiles is not met at 640** (§2): v4 must check tiles only where the screen changed. Fix the slow GPU start-up at 480 only if 480 is ever used (§4). |

---

## 2. Speed on the Redmi 12 (LiteRT `benchmark_model` over adb)

Full run 2026-10-07: every file × every applicable setting, 10 warm-up + 60 timed runs, 20 s pause between runs. **34 unique settings** (6 files × 6 settings, minus the 2 dynamic-range/fp16-math combinations); the CSV has 36 rows including 2 earlier repeats. Phone: Android 15, on the charger, screen on, battery **38–41 °C**. Raw: `bench/results/phone_latency.csv`, log `bench/results/bench_phone_all.log`.

**ms per full-screen check (average; p95 within ~5%) · peak memory in MB**

| Model file | CPU 4 thr | CPU 2 thr | CPU 1 thr | **CPU 2 thr, fp16 math** | **GPU** | NNAPI |
|---|---|---|---|---|---|---|
| 640 fp32 (10.6 MB) | 388 · 99 | 621 · 99 | 1141 · 99 | **277 · 87** | **205 · 182** | 1061 · 130 |
| 640 fp16 (5.4 MB) | 389 · 94 | 624 · 94 | 1187 · 95 | 310 · 83 | 207 · 177 | 1187 · 126 |
| 640 dynamic-range (3.0 MB) | 280 · 88 | 437 · 89 | 759 · 89 | — | 207 · 174 | 761 · 120 |
| 480 fp32 | 194 · 71 | 319 · 71 | 657 · 71 | **173 · 62** | **124 · 477** ⚠ | 658 · 102 |
| 480 fp16 | 196 · 67 | 311 · 67 | 590 · 67 | 154 · 58 | 121 · 473 ⚠ | 590 · 96 |
| 480 dynamic-range | 122 · 59 | 205 · 59 | 377 · 60 | — | 122 · 466 ⚠ | 380 · 88 |

GPU start-up time: **~4 s at 640**, but **~52–60 s at 480** with **~470 MB** peak memory (⚠, see §4). CPU start-up: 0.1–0.3 s.

**What this means**

- **The GPU (Mali-G52) is the fastest at 640: ~205 ms**, for every file type. On the CPU the best is **2 fast cores with fp16 math: 277 ms** (and lower memory, 87 MB).
- **NNAPI is useless on this phone**: as slow as 1 CPU thread. The Helio G88 has no AI unit that helps.
- **Heat slows the CPU a lot.** The same test (640 fp32, 4 threads) gave **295 ms at 35 °C** (2026-10-03), **301 ms at 37 °C** and **357 ms at 38 °C** (re-checked 2026-10-07), and **388 ms** in the warm full run. A filter that runs all day will run warm: plan with the warm numbers, and prefer the GPU or 2 threads.
- 4 threads use slow cores too: 2 threads with fp16 math are faster than 4 threads with fp32.
- **Decision rule (≤ 150 ms per full screen, so tiles fit): not met at 640.** Only 480 meets it (GPU 121 ms, CPU drq 122 ms), but 480 loses a lot of accuracy (§3). Consequence for v4: tiles at 640 cost ~3 × 205 ms ≈ 0.6 s on the GPU; check tiles only where the screen changed, or accept a longer wait in strict mode.

### 2.1 Sustained CPU/GPU test (2026-10-07)

Same **640 fp32** file, first CPU (2 threads, XNNPACK fp16 math), then GPU (OpenCL, all 477 nodes delegated). Each setting ran **15 consecutive 60-second timed blocks**, with one warm-up inference per block and no intentional cooling pauses. Model reloads between blocks add brief gaps (CPU ~0.1 s; GPU ~3–4 s): this is near-continuous load, not one persistent interpreter. Temperature and charging state were saved before and after every block; peak-memory monitoring was enabled.

The phone reported **AC charging throughout** (battery level 62% → 73%). GPU started immediately after CPU, on an already warm phone. Raw evidence: [`CSV`](../bench/results/phone_sustained_2026-10-07.csv), [`full log`](../bench/results/phone_sustained_2026-10-07.log).

| Setting | Timed inferences | Overall mean, ms | First → last block mean, ms | Highest block p95, ms | Peak memory, MB | Battery temperature, °C |
|---|---|---|---|---|---|---|
| CPU 2 threads, fp16 math | 3 436 | 261.4 | 220.1 → 260.9 | 411.9 | 87.4 | 34 → 40 |
| GPU | 4 729 | 189.3 | 182.8 → 191.6 | 203.3 | 181.6 | 40 → 38 (maximum 41) |

Overall means are weighted by inference count. The p95 column is the highest **per-minute** p95, not a pooled percentile over the full run.

- CPU averaged ~271–273 ms in blocks 4–13. Its final block had **p95 412 ms despite a 261 ms mean**: averages alone hide the jitter. GPU's final five blocks averaged ~188 ms, with no progressive slowdown in this run.
- **The ≤150 ms target still fails.** GPU remains the faster option, with tighter tail latency here; allow roughly 0.6 s for three model passes before capture, preprocessing, NMS and drawing costs.
- This is synthetic-input model inference, not app or battery-life testing. Charging, different starting temperatures and model reloads limit the comparison. Re-test with one persistent interpreter and the complete pipeline when the app exists.
- All 30 blocks completed with valid timing/memory data, no benchmark errors, CPU fp16 enabled and full GPU delegation. This closes the benchmark follow-up in issue #29.

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
| phone file, fp16 (640) | feed | whole / 3 tiles | 23.7 / **53.5** | 75.6 / 88.2 | 88.4 / 91.4 | | |
| | grid | whole / 3 tiles | 27.4 / **54.4** | 63.7 / 88.1 | 89.5 / 94.9 | | |
| phone file, fp32 (**480**) | feed | whole / 3 tiles | 22.8 / 39.5 | 63.0 / 84.3 | 78.9 / 90.1 | | |
| | grid | whole / 3 tiles | 15.8 / 42.7 | 40.8 / 81.2 | 76.8 / 93.2 | | |
| phone file, fp16 (480) | feed | whole / 3 tiles | 22.8 / 39.5 | 62.2 / 84.3 | 78.4 / 90.1 | | |
| | grid | whole / 3 tiles | 15.7 / 42.6 | 40.5 / 81.2 | 76.8 / 93.3 | | |
| phone file, dynamic-range (480) | feed | whole / 3 tiles | 22.8 / 37.7 | 56.7 / 82.7 | 77.2 / 89.2 | | |
| | grid | whole / 3 tiles | 14.4 / 42.3 | 38.7 / 80.8 | 77.2 / 93.3 | | |

### 3.2 What this means

- **The phone fp32 file works.** It matches the laptop model and is 1–4 points better (fp32 vs INT8).
- **fp16 is as accurate as fp32** (within 1 point), so the GPU can use the half-size file.
- **480 px loses a lot of accuracy**: in the grid, small 27 → 16%, medium 64 → 41%, large 89 → 77% (one pass). Even with tiles it stays below 640. **We keep 640.**
- **The dynamic-range file (3 MB, for the phone CPU) is almost as good as fp32**: within about 2 points, except small people in the feed with one pass (19.3 vs 23.7). With tiles the gap is under 3 points. If it is faster on the phone, it is the CPU choice.
- **Small people are the problem, as on Linux.** Half of the missed people are under about **40 px tall** on screen (38–44 px median, about 2.5 mm on a ~400 ppi screen). The model input is 640 px for a 2340 px tall screen, so the model sees them 3.7× smaller still: about 10 px. See `results/phone/missed_people_sheet.jpg`.
- **3 tiles roughly double small-person recall.** But they cost 3 checks: about 0.6 s on the GPU, more on the CPU.
- **Over-cover is high in the grid layout (≈40%)**, because small people get a cover that is big compared to them. That is acceptable: hiding too much is fine, showing a person is not.
- These are COCO photos on fake screens. Real app screenshots are still untested (v5).

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
| **GPU start-up at 480 px takes ~52–60 s and ~470 MB** (at 640: ~4 s, ~180 MB) | Every 480 file on the GPU; repeated twice on 2026-10-07 with the same result (52 s, 472 MB), so it is not a one-time effect | Do not use 480 on the GPU as is. If 480 is ever needed, try the GPU delegate's serialization cache (compiled kernels stored on disk) and re-measure. |
| **CPU speed drops with heat** | 640 fp32, 4 threads: 295 ms (35 °C) → 301 (37 °C) → 357 (38 °C) → 388 (warm full run) | Report warm numbers; record battery temperature with every phone result; prefer the GPU or 2 threads in the app |
| NNAPI gives no speed-up | NNAPI ≈ 1 CPU thread for every file | Do not use NNAPI on this phone |
| Phone model needs its own NMS | Output is 116 × 8400 boxes (the export does not include the de-duplication step) | The app must do NMS (a few lines). Same decode as `bench/ov_seg.py`. |

---

## 5. Done and still to do

**Done (2026-10-07):** full phone speed test (34 unique settings; 36 saved rows), accuracy of fp16 and 480 px files, sustained CPU/GPU test (15 minutes of timed inference each, §2.1). Both existing self-tests (`eval.py selftest`, `build_ar.py --test`) pass; Python compilation passes; rebuilding the 1 906-term word list reproduces the tracked file exactly. The existing six valid accuracy reports each contain 60 feed and 60 grid screens; these were audited, not re-run in the sustained-test session.

**Still to do (not blocking v1):**
- End-to-end sustained and battery-life testing with one persistent interpreter, when the app exists.
- GPU delegate serialization cache, only if 480 px or a new model shows the same slow GPU start-up.
- P0c (text models, v1.1): separate, see investigation §3.5.

---

## Reproducing

| What | Command (in `bench/`, after `source env.sh`) |
|---|---|
| Phone-screen accuracy, laptop model | `python phone.py ov-yolo:models/yolo26n-seg_int8_openvino_model/yolo26n-seg.xml:GPU 60` |
| Phone-screen accuracy, phone file | `python phone_tflite.py fp32 60` (or `fp16`, `drq`) |
| Export phone files | `python export_tflite.py` |
| Phone speed (adb, phone plugged in) | `python bench_phone.py [name filter]` |

For the sustained test, push `models_tflite/yolo26n-seg_640_fp32.tflite` to `/data/local/tmp/masking_sustained_640_fp32.tflite`. Run the following on the phone through `adb shell`, saving stdout and stderr to a new log; do not overwrite the recorded evidence. Remove that temporary model afterwards.

```sh
for cfg in cpu2_fp16 gpu; do
  if [ "$cfg" = gpu ]; then
    flags="--use_gpu=true"
  else
    flags="--num_threads=2 --use_xnnpack=true --xnnpack_force_fp16=true"
  fi
  i=1
  while [ "$i" -le 15 ]; do
    echo "SUSTAINED_BEGIN config=$cfg minute=$i"
    date -u
    dumpsys battery
    /data/local/tmp/benchmark_model \
      --graph=/data/local/tmp/masking_sustained_640_fp32.tflite $flags \
      --num_runs=1 --min_secs=60 --max_secs=65 \
      --warmup_runs=1 --warmup_min_secs=0 --report_peak_memory_footprint=true || exit 1
    dumpsys battery
    echo "SUSTAINED_END config=$cfg minute=$i"
    i=$((i+1))
  done
done
```
