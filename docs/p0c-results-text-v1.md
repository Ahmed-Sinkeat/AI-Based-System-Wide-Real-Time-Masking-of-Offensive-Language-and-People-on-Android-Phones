# P0c Results: Text Model on the Phone (step 1, quick)

Date: 2026-11-04 · Phone: Xiaomi Redmi 12 (Helio G88, Android 15, 8 GB), charging, battery 34 °C · Tool: LiteRT `benchmark_model`, 60 runs after 10 warm-up runs
Scope: **is a text model fast and small enough for layer ② (FR-20, NFR-13)?** Speed and memory only. The answer layer is random, so this says **nothing about accuracy** (that is P0c step 2, after training).

## 1. Bottom line

**Yes, it is possible.** The smallest candidate, **bert-mini-arabic** (11 M parameters after the vocabulary cut), checks one 64-token message in **~16 ms** with **~38 MB** of memory on the phone CPU. The target is ≤ 50 ms and ≤ 100 MB (NFR-13).

## 2. bert-mini-arabic, one message of 64 tokens

| File | Setting | Average | p95 | Peak memory |
|---|---|---|---|---|
| fp32 | CPU, 4 threads | **12.6 ms** | 14.3 ms | 38.6 MB |
| fp32 | CPU, 2 threads, fp16 math | **16.4 ms** | 16.7 ms | 38.3 MB |
| fp32 | CPU, 2 threads | 18.9 ms | 19.1 ms | 38.5 MB |
| fp32 | CPU, 1 thread | 34.7 ms | 35.1 ms | 38.4 MB |
| int8 weights | CPU, 2 threads | 29.3 ms | 30.5 ms | 38.5 MB |
| any | GPU, NNAPI | failed (export) | | |
| fp16 | all | failed (export) | | |

- **Best: fp32 on 2 cores with fp16 math, ~16 ms**, a third of the budget. Shorter messages are faster.
- **int8 is slower** (29 ms) for a model this small: not worth it.
- **GPU / NNAPI / fp16 failures come from the export**, not the model (sizes left dynamic; word table stored in fp16). Not needed: the CPU is fast enough, and the GPU is kept for the people model.
- **Export checked:** the phone file gives the same answer as the original model (difference < 1e-6 for fp32; int8 picks the same answer).

## 3. How it was measured

- Model: input 64 token ids → encoder → first token → linear layer with 5 outputs (random weights).
- Vocabulary cut to the first 30 000 entries, standing in for an Arabic-only cut.
- Export: PyTorch → ONNX → onnx2tf → LiteRT, script [`bench/export_text.py`](../bench/export_text.py); phone runs with [`bench/bench_phone.py`](../bench/bench_phone.py).

## 4. Next

- Same test for bert-medium-arabic, multilingual-e5-small and mmBERT-small (running).
- P0c step 2: quick training on a small Arabic set to compare accuracy.
