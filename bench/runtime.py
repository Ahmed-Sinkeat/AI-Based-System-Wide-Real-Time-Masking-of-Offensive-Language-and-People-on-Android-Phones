"""Daemon-like steady-state loop: the plugin hands over a window already downscaled to 640 long side.
Measures end-to-end ms (preprocess + infer + masks at 640x360), p50/p95/p99, process CPU%, RSS, GPU clock.

  python runtime.py <ov-spec> [seconds]      e.g. ov-yolo:models/yolo26n-seg_fp16_openvino_model/yolo26n-seg.xml:GPU
"""
import os, sys, time, json, threading
# Single-threaded post-processing: OpenBLAS/OpenCV thread pools otherwise spin ~7 cores (measured 729% CPU,
# p50 28 ms) for a 640x360 frame; with 1 thread: 100% CPU, p50 22 ms. Must be set before numpy is imported.
for v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS"): os.environ.setdefault(v, "1")
from pathlib import Path
import numpy as np, cv2, psutil
import ov_seg
cv2.setNumThreads(1)

spec, secs = sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 45
pred = ov_seg.make(spec)
frames = []
for p in sorted(Path("data/val2017").glob("*.jpg"))[:64]:
    im = cv2.imread(str(p)); frames.append(cv2.resize(im, (640, 360), interpolation=cv2.INTER_AREA))

for f in frames[:10]:  # warm-up (GPU kernels, caches)
    pred(f)

freq, stop = [], threading.Event()
def sample_freq():
    while not stop.is_set():
        try: freq.append(int(Path("/sys/class/drm/card1/gt_act_freq_mhz").read_text()))
        except OSError: pass
        time.sleep(0.2)
threading.Thread(target=sample_freq, daemon=True).start()

proc = psutil.Process(); proc.cpu_percent(); psutil.cpu_percent()
lat, i, t_end = [], 0, time.time() + secs
while time.time() < t_end:
    t0 = time.perf_counter()
    dets = [d for d in pred(frames[i % len(frames)]) if d[0] >= 0.25]
    lat.append((time.perf_counter() - t0) * 1e3); i += 1
stop.set()
lat = np.array(lat)
import subprocess
contended = subprocess.run(["pgrep", "-f", "render.py"], capture_output=True).returncode == 0
out = dict(spec=spec, contended=contended, frames=int(len(lat)), fps=float(len(lat) / secs),
           p50_ms=float(np.percentile(lat, 50)), p95_ms=float(np.percentile(lat, 95)), p99_ms=float(np.percentile(lat, 99)),
           max_ms=float(lat.max()), proc_cpu_pct_of_one_core=proc.cpu_percent(), system_cpu_pct=psutil.cpu_percent(),
           rss_mb=proc.memory_info().rss / 2**20, gpu_mhz_median=float(np.median(freq)) if freq else None,
           gpu_mhz_max_possible=int(Path("/sys/class/drm/card1/gt_max_freq_mhz").read_text()))
print(json.dumps(out, indent=1))
Path("results").mkdir(exist_ok=True)
(Path("results") / f"runtime__{spec.replace('/', '_').replace(':', '_')}.json").write_text(json.dumps(out, indent=1))
