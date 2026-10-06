"""INT8 post-training quantization of RF-DETR-Seg IR with NNCF (same coco128 calibration images as the YOLO INT8 exports)."""
import sys
from pathlib import Path
import numpy as np, cv2, nncf, openvino as ov
from nncf.quantization.advanced_parameters import AdvancedQuantizationParameters, AdvancedSmoothQuantParameters
from ov_seg import MEAN, STD

for tag in sys.argv[1:] or ["rfdetrsegnano", "rfdetrsegsmall"]:
    src, dst = Path(f"models/{tag}_fp16/model.xml"), Path(f"models/{tag}_int8/model.xml")
    if dst.exists():
        continue
    model = ov.Core().read_model(src)
    sz = model.inputs[0].get_partial_shape()[2].get_length()
    def prep(p):
        x = cv2.resize(cv2.imread(str(p))[:, :, ::-1], (sz, sz)).astype(np.float32) / 255
        return ((x - MEAN) / STD).transpose(2, 0, 1)[None].astype(np.float32)
    imgs = sorted(Path("datasets/coco128-seg/images/train2017").glob("*.jpg"))
    # ponytail: plain PTQ with transformer preset; try accuracy-aware QAT only if INT8 recall drops > ~2 points
    q = nncf.quantize(model, nncf.Dataset(imgs, prep), model_type=nncf.ModelType.TRANSFORMER, subset_size=len(imgs),
                       # SmoothQuant must be OFF: with it, RF-DETR INT8 collapses to AP 0.000 (measured); without, 0.437 vs FP16 0.446
                       advanced_parameters=AdvancedQuantizationParameters(
                           smooth_quant_alphas=AdvancedSmoothQuantParameters(matmul=-1)))
    dst.parent.mkdir(exist_ok=True); ov.save_model(q, dst)
    print("quantized", tag)
