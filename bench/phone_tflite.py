"""phone.py's fake-phone-screen accuracy test, but with the actual phone .tflite file (run on the laptop with LiteRT).
Checks that the exported phone model finds the same people as the OpenVINO model.  Decode = ov_seg.yolo (same NMS).

  python phone_tflite.py <variant> [n_screens]     variant = fp32 | fp16 | drq   (models_tflite/yolo26n-seg_640_<variant>.tflite)
Writes results/phone_tflite_<variant>/ (does not touch results/phone/)."""
import sys, numpy as np
from pathlib import Path
import ov_seg, phone
from ai_edge_litert.interpreter import Interpreter


def tflite_compile(path, dev):  # stands in for ov_seg.compile: NCHW in, [boxes 1x116xN, protos 1x32x160x160] out
    it = Interpreter(path, num_threads=4); it.allocate_tensors()
    i, outs = it.get_input_details()[0]["index"], it.get_output_details()
    o0 = [d["index"] for d in outs if len(d["shape"]) == 3][0]; o1 = [d["index"] for d in outs if len(d["shape"]) == 4][0]
    def run(x):
        it.set_tensor(i, np.ascontiguousarray(x.transpose(0, 2, 3, 1))); it.invoke()
        return [it.get_tensor(o0), it.get_tensor(o1).transpose(0, 3, 1, 2)]
    return run


if __name__ == "__main__":
    k = sys.argv[1]
    ov_seg.compile = tflite_compile
    phone.make_predictor = lambda spec: ov_seg.yolo(f"models_tflite/yolo26n-seg_640_{k}.tflite", "CPU")
    phone.OUT = Path(f"results/phone_tflite_{k}"); phone.OUT.mkdir(parents=True, exist_ok=True)
    phone.main(f"tflite-{k}", int(sys.argv[2]) if len(sys.argv) > 2 else 60)
