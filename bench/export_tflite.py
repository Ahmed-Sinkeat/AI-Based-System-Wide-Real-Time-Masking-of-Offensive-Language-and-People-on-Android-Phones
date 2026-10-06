"""Export phone candidates to LiteRT (.tflite) for on-device benchmarking: ONNX -> onnx2tf.
float32 / float16 -> phone GPU delegate, dynamic_range_quant (INT8 weights, float math) -> phone CPU.
Full INT8 (integer_quant) is BROKEN for this head: boxes (0..640) and class scores (0..1) share one output tensor and one
quantization scale, so every score rounds to 0 and the model finds nobody (checked 2026-10-06: 0/448 vs float32).
onnx2tf 2.x: INT8 needs our own calibration data (-cind); tf_converter backend for full quantization support.
Ultralytics' own litert export auto-installs litert-torch, which forces torch < 2.14 -> avoided on purpose."""
import shutil, subprocess, glob
from pathlib import Path
import numpy as np, cv2
from ultralytics import YOLO

def calib(sz, n=100):  # coco128 letterboxed like YOLO preprocessing, NHWC float 0..1
    xs = []
    for p in sorted(Path("datasets/coco128-seg/images/train2017").glob("*.jpg"))[:n]:
        im = cv2.imread(str(p))[:, :, ::-1]; r = min(sz / im.shape[0], sz / im.shape[1])
        nw, nh = round(im.shape[1] * r), round(im.shape[0] * r); lb = np.full((sz, sz, 3), 114, np.uint8)
        lb[(sz - nh) // 2:(sz - nh) // 2 + nh, (sz - nw) // 2:(sz - nw) // 2 + nw] = cv2.resize(im, (nw, nh))
        xs.append(lb.astype(np.float32) / 255)
    f = Path(f"tflite_work/calib_{sz}.npy"); f.parent.mkdir(exist_ok=True); np.save(f, np.stack(xs)); return f

OUT = Path("models_tflite"); OUT.mkdir(exist_ok=True)
JOBS = [("yolo26n-seg", 640), ("yolo26n-seg", 480), ("yolo26n-seg", 320), ("yolo11n-seg", 640), ("yolo26s-seg", 640)]
for name, sz in JOBS:
    # ponytail: no full INT8, export with boxes divided by imgsz (as Ultralytics' own tflite export does) if CPU speed needs it
    want = {"fp32": "*_float32.tflite", "fp16": "*_float16.tflite", "drq": "*_dynamic_range_quant.tflite"}
    if all((OUT / f"{name}_{sz}_{k}.tflite").exists() for k in want):
        continue
    onnx = Path(YOLO(f"{name}.pt").export(format="onnx", imgsz=sz, simplify=True, verbose=False))
    work = Path(f"tflite_work/{name}_{sz}"); shutil.rmtree(work, ignore_errors=True)
    # ponytail: coco128 calibration, use screen-domain frames once we have them
    r = subprocess.run(["../.venv/bin/onnx2tf", "-i", str(onnx), "-o", str(work), "-tb", "tf_converter", "-oiqt",
                        "-cind", "images", str(calib(sz)), "[[[[0,0,0]]]]", "[[[[1,1,1]]]]"], capture_output=True, text=True)
    for k, pat in want.items():
        hits = glob.glob(str(work / pat))
        if not hits:
            print("FAILED", name, sz, k, r.stdout[-400:], r.stderr[-400:]); continue
        dst = OUT / f"{name}_{sz}_{k}.tflite"; shutil.copy(hits[0], dst)
        print("exported", dst, f"{dst.stat().st_size / 2**20:.1f} MB", flush=True)
