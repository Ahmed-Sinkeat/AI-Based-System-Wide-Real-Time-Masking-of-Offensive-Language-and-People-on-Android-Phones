"""Export candidate seg models to OpenVINO IR (FP16 + INT8). Run from bench/ with env.sh sourced."""
import sys, glob, shutil
from pathlib import Path
import openvino as ov

OUT = Path("models"); OUT.mkdir(exist_ok=True)
which = sys.argv[1:] or ["yolo", "rfdetr"]

if "yolo" in which:
    from ultralytics import YOLO
    for name in ["yolo11n-seg", "yolo11s-seg", "yolo26n-seg", "yolo26s-seg"]:
        for int8 in (False, True):
            tag = f"{name}_{'int8' if int8 else 'fp16'}"
            tag += "_openvino_model"  # ultralytics detects the backend by this suffix
            if (OUT / tag).exists():
                continue
            m = YOLO(f"{name}.pt")
            # ponytail: coco128-seg as INT8 calibration set (128 imgs), use screen-domain frames once we have them
            p = m.export(format="openvino", imgsz=640, half=not int8, int8=int8,
                         data="coco128-seg.yaml" if int8 else None, verbose=False)
            shutil.move(p, OUT / tag)
            print("exported", tag)

if "rfdetr" in which:
    import rfdetr, numpy as np
    from PIL import Image
    for cls in ["RFDETRSegNano", "RFDETRSegSmall", "RFDETRSegMedium"]:
        tag = cls.lower()
        if (OUT / f"{tag}_fp16" / "model.xml").exists():
            continue
        m = getattr(rfdetr, cls)()
        res = m.model_config.resolution
        d = OUT / f"{tag}_onnx"; d.mkdir(exist_ok=True)
        m.export(output_dir=str(d))
        onnx = glob.glob(str(d / "*.onnx"))[0]
        model = ov.convert_model(onnx)
        (OUT / f"{tag}_fp16").mkdir(exist_ok=True)
        ov.save_model(model, OUT / f"{tag}_fp16" / "model.xml", compress_to_fp16=True)
        (OUT / f"{tag}_fp16" / "res.txt").write_text(str(res))
        print("exported", tag, "res", res, [i.get_partial_shape() for i in model.inputs])
