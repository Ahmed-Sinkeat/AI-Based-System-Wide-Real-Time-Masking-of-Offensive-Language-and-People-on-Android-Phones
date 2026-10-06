"""Raw model latency on CPU and Iris Xe GPU via OpenVINO benchmark_app (batch 1, latency hint).
Writes results/latency.csv. Run from bench/ with env.sh sourced, machine otherwise idle."""
import re, subprocess, csv, sys
from pathlib import Path

Path("results").mkdir(exist_ok=True)
rows = []
def contended():  # another GPU/CPU-heavy job running? (timings then not trustworthy)
    return subprocess.run(["pgrep", "-f", "render.py"], capture_output=True).returncode == 0
for xml in sorted(Path("models").glob("*/*.xml")):
    tag = xml.parent.name
    if tag.endswith("_onnx") or (sys.argv[1:] and not any(a in tag for a in sys.argv[1:])):
        continue
    for dev in ("GPU", "CPU"):
        cmd = ["benchmark_app", "-m", str(xml), "-d", dev, "-hint", "latency", "-t", "20", "-cdir", "ovcache"]  # warm cache: avoids flaky cold IGC compiles
        for attempt in range(3):  # GPU runs failed transiently while another job used the iGPU
            r = subprocess.run(cmd, capture_output=True, text=True); out = r.stdout + r.stderr
            if "Median" in out:
                break
        def grab(key):
            m = re.search(rf"{key}:\s+([\d.]+) ms", out)
            return float(m.group(1)) if m else None
        thr = re.search(r"Throughput:\s+([\d.]+) FPS", out)
        shape = re.search(r"\[(1,3,\d+,\d+)\]", out)
        comp = re.search(r"Compile model took ([\d.]+) ms", out)
        row = dict(model=tag, device=dev, compile_ms=float(comp.group(1)) if comp else None, median_ms=grab("Median"), avg_ms=grab("Average"),
                   min_ms=grab("Min"), max_ms=grab("Max"), fps=float(thr.group(1)) if thr else None,
                   input=shape.group(1).strip() if shape else "")
        if row["median_ms"] is None:
            row["input"] = "FAILED: " + (out[-300:] or "no output").replace("\n", " ")
        row["contended"] = contended()
        print(row, flush=True)
        rows.append(row)

new = not Path("results/latency.csv").exists()
with open("results/latency.csv", "a", newline="") as f:  # appends; `python latency.py <tag substr>` adds models
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    if new: w.writeheader()
    w.writerows(rows)
