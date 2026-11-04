"""Cover-gap test: how long is the magenta test word (ZQXJ) visible without a cover in a screen recording?
screenrecord only writes a frame when the screen changes, so each frame lasts until the next frame's timestamp.
Usage: ../.venv/bin/python gap_frames.py results/probe_gap.mp4 PHASE_SPLIT_SECONDS"""
import subprocess, sys
import cv2

path, split = sys.argv[1], float(sys.argv[2])
ts = [float(x) for x in subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "frame=pts_time",
                                        "-of", "csv=p=0", path], capture_output=True, text=True).stdout.split()]
cap, mag = cv2.VideoCapture(path), []
while True:
    ok, f = cap.read()
    if not ok: break
    b, g, r = (f[..., i].astype(int) for i in range(3))
    mag.append(int(((r > 180) & (b > 180) & (g < 90)).sum()))
n = min(len(ts), len(mag)); ts, mag = ts[:n], mag[:n]
assert n > 10 and max(mag) > 1000, "no magenta word found in the video: the test screen is wrong"
TH = 200  # ponytail: fixed pixel threshold; one fully visible ZQXJ is ~2 000-3 000 px at this text size

eps, start = [], None
for i in range(n + 1):
    on = i < n and mag[i] > TH
    if on and start is None: start = i
    if not on and start is not None:
        end = ts[i] if i < n else ts[-1]; eps.append((ts[start], (end - ts[start]) * 1000, i - start)); start = None
for name, lo, hi in (("appear", 0, split), ("scroll", split, 1e9)):
    e = [x for x in eps if lo <= x[0] < hi]
    print(f"{name}: {len(e)} times visible, total {sum(d for _, d, _ in e):.0f} ms, longest {max([d for _, d, _ in e], default=0):.0f} ms, "
          f"frames per time {sorted(k for *_, k in e)}")
