"""Torch-free OpenVINO person-segmentation predictors (this is the daemon's runtime path).
Torch must NOT be imported in the same process: its bundled LLVM clashes with Intel's GPU compiler (IGC).

make(spec) -> pred(img_bgr) -> [(score, mask bool HxW, box xyxy)], person only.
spec: ov-yolo:<xml>:<CPU|GPU>  or  ov-rfdetr:<xml>:<CPU|GPU>
"""
import numpy as np, cv2
import openvino as ov

MEAN = np.array([0.485, 0.456, 0.406], np.float32); STD = np.array([0.229, 0.224, 0.225], np.float32)
sig = lambda x: 1 / (1 + np.exp(-x))


def compile(xml, dev):
    core = ov.Core(); core.set_property({"CACHE_DIR": "ovcache"})
    return core.compile_model(xml, dev, {"PERFORMANCE_HINT": "LATENCY"})


def yolo(xml, dev, conf=0.05, iou=0.7, sz=640):
    m = compile(xml, dev)

    def pred(img):
        H, W = img.shape[:2]
        r = min(sz / H, sz / W); nw, nh = round(W * r), round(H * r)
        px, py = (sz - nw) / 2, (sz - nh) / 2
        l, t = round(px - 0.1), round(py - 0.1)
        lb = np.full((sz, sz, 3), 114, np.uint8)
        lb[t:t + nh, l:l + nw] = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
        x = lb[:, :, ::-1].transpose(2, 0, 1)[None].astype(np.float32) / 255
        out = m(x); o0, proto = out[0][0], out[1][0]                       # proto: 32 x 160 x 160
        if o0.shape[0] == 116:                                              # YOLO11: 116 x 8400, needs NMS
            o0 = o0.T
            s = o0[:, 4]; k = s >= conf
            b, s, coef = o0[k, :4], s[k], o0[k, 84:]
            xyxy = np.c_[b[:, :2] - b[:, 2:] / 2, b[:, :2] + b[:, 2:] / 2]
            keep = cv2.dnn.NMSBoxes(np.c_[xyxy[:, :2], b[:, 2:]].tolist(), s.tolist(), conf, iou)
            keep = np.array(keep, int).reshape(-1)
            xyxy, s, coef = xyxy[keep], s[keep], coef[keep]
        else:                                                               # YOLO26 end2end: 300 x (xyxy, score, cls, 32 coef)
            k = (o0[:, 4] >= conf) & (o0[:, 5] == 0)
            xyxy, s, coef = o0[k, :4], o0[k, 4], o0[k, 6:]
        order = np.argsort(-s)[:50]; xyxy, s, coef = xyxy[order], s[order], coef[order]
        res = []
        if not len(s):
            return res
        pm = sig(coef @ proto.reshape(32, -1)).reshape(-1, *proto.shape[1:])  # N x 160 x 160
        xyxy = (xyxy - [l, t, l, t]) / r                                    # to original image coords
        xyxy = np.clip(xyxy, 0, [W, H, W, H])
        for si, bi, mi in zip(s, xyxy, pm):
            mi = cv2.resize(mi, (sz, sz), interpolation=cv2.INTER_LINEAR)[t:t + nh, l:l + nw]
            mi = cv2.resize(mi, (W, H), interpolation=cv2.INTER_LINEAR) > 0.5
            x0, y0, x1, y1 = np.round(bi).astype(int)
            crop = np.zeros_like(mi); crop[y0:y1, x0:x1] = True
            res.append((float(si), mi & crop, bi))
        return res
    return pred


def rfdetr(xml, dev, conf=0.05):
    m = compile(xml, dev)
    sz = m.inputs[0].get_partial_shape()[2].get_length()

    def pred(img):
        H, W = img.shape[:2]
        x = cv2.resize(img[:, :, ::-1], (sz, sz), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255
        x = ((x - MEAN) / STD).transpose(2, 0, 1)[None]
        out = m(x); boxes, logits, masks = out[0][0], out[1][0], out[2][0]
        s = sig(logits[:, 1])                                               # COCO category id 1 = person
        k = np.argsort(-s); k = k[s[k] >= conf][:50]
        res = []
        for i in k:
            cx, cy, w, h = boxes[i]
            b = np.clip(np.array([(cx - w / 2) * W, (cy - h / 2) * H, (cx + w / 2) * W, (cy + h / 2) * H]), 0, [W, H, W, H])
            mk = cv2.resize(masks[i], (W, H), interpolation=cv2.INTER_LINEAR) > 0
            res.append((float(s[i]), mk, b))
        return res
    return pred


def make(spec):
    kind, xml, dev = spec.split(":")
    return {"ov-yolo": yolo, "ov-rfdetr": rfdetr}[kind](xml, dev)
