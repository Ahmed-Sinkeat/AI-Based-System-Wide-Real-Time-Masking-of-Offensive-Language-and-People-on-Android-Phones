"""On-phone latency + RAM via LiteRT benchmark_model over adb. Writes results/phone_latency.csv.
Phone should be idle and screen on. A 20 s pause between runs limits thermal throttling (the phone has no fan)."""
import re, csv, subprocess, sys, time
from pathlib import Path

D = "/data/local/tmp"
CONFIGS = {"cpu4": "--num_threads=4", "cpu2": "--num_threads=2", "cpu1": "--num_threads=1", "gpu": "--use_gpu=true",
           "nnapi": "--use_nnapi=true",
           "cpu2_fp16": "--num_threads=2 --use_xnnpack=true --xnnpack_force_fp16=true"}  # A75 cores have FP16 math
adb = lambda *a, **k: subprocess.run(["adb", *a], capture_output=True, text=True, **k)
temp = lambda: (re.search(r"temperature: (\d+)", adb("shell", "dumpsys battery").stdout) or [None, None])[1]  # 0.1 C; thermal_zone is locked

OUT = Path("results/phone_latency.csv"); OUT.parent.mkdir(exist_ok=True)

def save(row):  # one row at a time, so a crash or unplugged phone keeps what already ran
    new = not OUT.exists()
    with open(OUT, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row)); new and w.writeheader(); w.writerow(row)

models = sorted(Path("models_tflite").glob("*.tflite"))
for m in models:
    if sys.argv[1:] and not any(a in m.name for a in sys.argv[1:]):
        continue
    adb("push", str(m), f"{D}/{m.name}")
    for cfg, flag in CONFIGS.items():
        if cfg.endswith("fp16") and "drq" in m.name:  # force_fp16 is for float models only
            continue
        time.sleep(20)
        r = adb("shell", f"{D}/benchmark_model --graph={D}/{m.name} {flag} --num_runs=60 --warmup_runs=10 "
                         f"--report_peak_memory_footprint=true", timeout=900)
        out = r.stdout + r.stderr
        g = lambda pat: (lambda x: float(x.group(1)) if x else None)(re.search(pat, out))
        main = ([l for l in out.splitlines() if "count=" in l] or [""])[-1]  # last count= line = main run (first is warm-up)
        st = lambda k: (lambda x: float(x.group(1)) / 1000 if x else None)(re.search(rf"\b{k}=(\d+)", main))
        row = dict(model=m.stem, config=cfg, size_mb=round(m.stat().st_size / 2**20, 1),
                   avg_ms=(g(r"Inference \(avg\): ([\d.e+]+)") or 0) / 1000 or None,
                   std_ms=st("std"), p95_ms=st("p95"), max_ms=st("max"),
                   init_ms=(g(r"Init: ([\d.e+]+)") or 0) / 1000 or None,
                   peak_mem_mb=g(r"Overall peak memory footprint \(MB\) via periodic monitoring: ([\d.]+)"),
                   delegated=" + ".join(f"{x}/{y}" for x, y in re.findall(r"Replacing (\d+) out of (\d+) node", out)) or None,  # nodes on accelerator
                   batt_temp_dC=temp(),
                   note="" if "Inference (avg)" in out else "FAILED: " + out[-200:].replace("\n", " "))
        print(row, flush=True); save(row)
    adb("shell", f"rm {D}/{m.name}")

