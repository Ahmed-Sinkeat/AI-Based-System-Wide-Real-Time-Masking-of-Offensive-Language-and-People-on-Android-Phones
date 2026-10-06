"""Person-only accuracy, measured the way the product cares about (coverage of person pixels), plus COCO mask AP.

  python eval.py coco   <spec> [limit]   # COCO val2017: person images + 500 person-free images
  python eval.py screen <spec> [n]       # synthetic 1920x1080 "feed window" of 6 COCO tiles, full vs 2x2 tiled
  python eval.py selftest                # metric sanity check, no model

spec: yolo:<ov_dir>:<device>   e.g. yolo:models/yolo11n-seg_fp16:intel:gpu
      rfdetr:<Class>           e.g. rfdetr:RFDETRSegNano   (PyTorch CPU)
      ov-yolo:<xml>:<CPU|GPU>, ov-rfdetr:<xml>:<CPU|GPU>   torch-free runtime path (see ov_seg.py)
"""
import sys, json, time, random
from pathlib import Path
import numpy as np, cv2

THRS = [0.1, 0.25, 0.4, 0.5]
BUCKETS = [("small", 0, 32**2), ("medium", 32**2, 96**2), ("large", 96**2, 1e18)]
DATA = Path("data")


# ---------------- predictors: img(BGR ndarray) -> list of (score, mask bool HxW, box xyxy) ----------------
def make_predictor(spec):
    kind, rest = spec.split(":", 1)
    if kind.startswith("ov-"):
        import ov_seg
        return ov_seg.make(spec)
    if kind == "yolo":
        path, dev = rest.split(":", 1)
        from ultralytics import YOLO
        m = YOLO(path, task="segment")
        def pred(img):
            r = m.predict(img, imgsz=640, conf=0.05, classes=[0], retina_masks=True, device=dev,
                          verbose=False, max_det=50)[0]
            if r.masks is None:
                return []
            ms = r.masks.data.cpu().numpy() > 0.5
            return list(zip(r.boxes.conf.cpu().numpy().tolist(), ms, r.boxes.xyxy.cpu().numpy()))
        return pred
    if kind == "rfdetr":
        import rfdetr
        from PIL import Image
        m = getattr(rfdetr, rest)()
        m.optimize_for_inference() if hasattr(m, "optimize_for_inference") else None
        def pred(img):
            d = m.predict(Image.fromarray(img[:, :, ::-1]), threshold=0.05)
            keep = d.class_id == 1  # COCO category id 1 = person
            if d.mask is None or not keep.any():
                return []
            return list(zip(d.confidence[keep].tolist(), d.mask[keep], d.xyxy[keep]))
        return pred
    raise ValueError(spec)


# ---------------- metrics ----------------
def regions(dets, thr, shape):
    """Three render modes for the blur region: raw mask, dilated mask, filled boxes."""
    H, W = shape
    mask = np.zeros((H, W), bool); box = np.zeros((H, W), bool)
    for s, m, b in dets:
        if s < thr:
            continue
        mask |= m
        x0, y0, x1, y1 = np.clip(np.round(b).astype(int), 0, [W, H, W, H])
        box[y0:y1, x0:x1] = True
    k = max(3, round(0.01 * max(H, W))) | 1  # ~1% of long side
    dil = cv2.dilate(mask.astype(np.uint8), np.ones((k, k), np.uint8)).astype(bool)
    return {"mask": mask, "mask_dil": dil, "box": box}


def new_acc():
    return {"inst": {b[0]: [] for b in BUCKETS}, "gt_px": 0, "cov_px": 0, "pred_px": 0, "over_px": 0,
            "neg_imgs": 0, "neg_alarm": 0, "neg_frac": 0.0}


def accumulate(acc, inst_masks, inst_areas, crowd, pred):
    gt = np.zeros(pred.shape, bool)
    for m, a in zip(inst_masks, inst_areas):
        gt |= m
        cov = (m & pred).sum() / max(1, m.sum())
        acc["inst"][next(n for n, lo, hi in BUCKETS if lo <= a < hi)].append(cov)
    acc["gt_px"] += int(gt.sum()); acc["cov_px"] += int((gt & pred).sum())
    acc["pred_px"] += int(pred.sum()); acc["over_px"] += int((pred & ~(gt | crowd)).sum())


def summarize(acc):
    out = {}
    for b, covs in acc["inst"].items():
        c = np.array(covs)
        out[b] = dict(n=len(c), rec50=float((c >= 0.5).mean()) if len(c) else None,
                      rec90=float((c >= 0.9).mean()) if len(c) else None)
    out["pixel_recall"] = acc["cov_px"] / max(1, acc["gt_px"])
    out["overblur"] = acc["over_px"] / max(1, acc["pred_px"])
    if acc["neg_imgs"]:
        out["neg_false_alarm_rate"] = acc["neg_alarm"] / acc["neg_imgs"]
        out["neg_blurred_area"] = acc["neg_frac"] / acc["neg_imgs"]
    return out


# ---------------- COCO val2017 ----------------
def run_coco(spec, limit=None):
    from pycocotools.coco import COCO
    from pycocotools.cocoeval import COCOeval
    from pycocotools import mask as mu
    coco = COCO(str(DATA / "annotations/instances_val2017.json"))
    pos = sorted(coco.getImgIds(catIds=[1]))
    neg = sorted(set(coco.getImgIds()) - set(pos))
    random.Random(0).shuffle(neg); neg = neg[:500]
    if limit:
        pos, neg = pos[:limit], neg[:max(1, limit // 5)]
    pred = make_predictor(spec)
    accs = {(t, mode): new_acc() for t in THRS for mode in ("mask", "mask_dil", "box")}
    results, times = [], []
    for i, iid in enumerate(pos + neg):
        info = coco.loadImgs(iid)[0]
        img = cv2.imread(str(DATA / "val2017" / info["file_name"]))
        t0 = time.perf_counter(); dets = pred(img); times.append(time.perf_counter() - t0)
        H, W = img.shape[:2]
        anns = coco.loadAnns(coco.getAnnIds(imgIds=iid, catIds=[1], iscrowd=None))
        inst = [(coco.annToMask(a).astype(bool), a["area"]) for a in anns if not a["iscrowd"]]
        crowd = np.zeros((H, W), bool)
        for a in anns:
            if a["iscrowd"]:
                crowd |= coco.annToMask(a).astype(bool)
        for s, m, b in dets:
            rle = mu.encode(np.asfortranarray(m.astype(np.uint8))); rle["counts"] = rle["counts"].decode()
            results.append(dict(image_id=iid, category_id=1, segmentation=rle, score=float(s)))
        for t in THRS:
            for mode, r in regions(dets, t, (H, W)).items():
                acc = accs[(t, mode)]
                if iid in neg:
                    acc["neg_imgs"] += 1; acc["neg_alarm"] += int(r.any()); acc["neg_frac"] += r.mean()
                else:
                    accumulate(acc, [m for m, _ in inst], [a for _, a in inst], crowd, r)
        if i % 250 == 0:
            print(f"{i}/{len(pos)+len(neg)} {np.median(times)*1e3:.1f} ms/img", flush=True)

    ap = {}
    if results:
        E = COCOeval(coco, coco.loadRes(results), "segm")
        E.params.catIds = [1]; E.params.imgIds = pos
        E.evaluate(); E.accumulate(); E.summarize()
        ap = dict(AP=E.stats[0], AP50=E.stats[1], AP_small=E.stats[3], AP_medium=E.stats[4], AP_large=E.stats[5],
                  AR100=E.stats[8])
    out = dict(spec=spec, n_pos=len(pos), n_neg=len(neg), e2e_ms_median=float(np.median(times) * 1e3),
               person_mask_ap=ap,
               by_thr={f"{t}/{mode}": summarize(a) for (t, mode), a in accs.items()})
    save(out, "coco", spec)


# ---------------- synthetic screen feed ----------------
def run_screen(spec, n=100):
    """1920x1080 window, header bar, 3x2 grid of photo tiles, like a social feed / search results page.
    Compares one 640 pass over the whole window (the plugin's default) with a 2x2 tiled pass."""
    from pycocotools.coco import COCO
    coco = COCO(str(DATA / "annotations/instances_val2017.json"))
    pos = sorted(coco.getImgIds(catIds=[1])); random.Random(1).shuffle(pos)
    pred = make_predictor(spec)
    W, H, TW, TH = 1920, 1080, 600, 440
    accs = {(v, t): new_acc() for v in ("full", "tiled2x2") for t in THRS}
    times = {"full": [], "tiled2x2": []}
    for c in range(n):
        canvas = np.full((H, W, 3), 245, np.uint8); canvas[:80] = (60, 60, 60)
        inst, areas, crowd = [], [], np.zeros((H, W), bool)
        for k, iid in enumerate(pos[c * 6:(c + 1) * 6]):
            info = coco.loadImgs(iid)[0]
            img = cv2.imread(str(DATA / "val2017" / info["file_name"]))
            s = min(TW / img.shape[1], TH / img.shape[0])
            w, h = int(img.shape[1] * s), int(img.shape[0] * s)
            x0, y0 = 30 + (k % 3) * (TW + 30), 110 + (k // 3) * (TH + 30)
            canvas[y0:y0 + h, x0:x0 + w] = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)
            cv2.putText(canvas, f"post #{c*6+k}  some caption text", (x0, y0 + h + 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (40, 40, 40), 1)
            for a in coco.loadAnns(coco.getAnnIds(imgIds=iid, catIds=[1], iscrowd=None)):
                m = np.zeros((H, W), bool)
                m[y0:y0 + h, x0:x0 + w] = cv2.resize(coco.annToMask(a), (w, h), interpolation=cv2.INTER_NEAREST) > 0
                if a["iscrowd"]:
                    crowd |= m
                elif m.any():
                    inst.append(m); areas.append(int(m.sum()))
        for v in ("full", "tiled2x2"):
            t0 = time.perf_counter()
            if v == "full":
                dets = pred(canvas)
            else:
                dets, ov = [], 64  # 2x2 tiles with 64 px overlap
                for ty in (0, 1):
                    for tx in (0, 1):
                        xa, ya = max(0, tx * W // 2 - ov), max(0, ty * H // 2 - ov)
                        xb, yb = min(W, (tx + 1) * W // 2 + ov), min(H, (ty + 1) * H // 2 + ov)
                        for s, m, b in pred(np.ascontiguousarray(canvas[ya:yb, xa:xb])):
                            full = np.zeros((H, W), bool); full[ya:yb, xa:xb] = m
                            dets.append((s, full, b + [xa, ya, xa, ya]))
            times[v].append(time.perf_counter() - t0)
            for t in THRS:
                accumulate(accs[(v, t)], inst, areas, crowd, regions(dets, t, (H, W))["mask_dil"])
        if c % 20 == 0:
            print(f"canvas {c}/{n}", flush=True)
    out = dict(spec=spec, canvases=n, mode="mask_dil",
               e2e_ms_median={v: float(np.median(x) * 1e3) for v, x in times.items()},
               by_thr={f"{v}/{t}": summarize(a) for (v, t), a in accs.items()})
    save(out, "screen", spec)


def save(out, kind, spec):
    Path("results").mkdir(exist_ok=True)
    p = Path("results") / f"{kind}__{spec.replace('/', '_').replace(':', '_')}.json"
    p.write_text(json.dumps(out, indent=1))
    print("wrote", p)


def selftest():
    H = W = 100
    gt = np.zeros((H, W), bool); gt[10:50, 10:50] = True           # 1600 px instance, medium bucket
    dets = [(0.9, gt.copy(), np.array([10, 10, 50, 50.])), (0.2, np.zeros((H, W), bool), np.array([60, 60, 70, 70.]))]
    r = regions(dets, 0.25, (H, W))
    assert r["mask"].sum() == 1600 and r["box"].sum() == 1600 and r["mask_dil"].sum() > 1600
    acc = new_acc(); accumulate(acc, [gt], [1600], np.zeros((H, W), bool), r["mask"])
    s = summarize(acc)
    assert s["medium"]["rec90"] == 1.0 and s["pixel_recall"] == 1.0 and s["overblur"] == 0.0
    r = regions(dets, 0.1, (H, W))                                  # low thr: second box appears
    acc = new_acc(); half = gt.copy(); half[30:50] = False          # prediction covers half the person
    accumulate(acc, [gt], [1600], np.zeros((H, W), bool), half | r["box"] & ~gt)
    s = summarize(acc)
    assert s["medium"]["rec50"] == 1.0 and s["medium"]["rec90"] == 0.0 and abs(s["pixel_recall"] - 0.5) < 1e-9
    assert abs(s["overblur"] - 100 / 900) < 1e-9
    print("selftest ok")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "selftest":
        selftest()
    elif cmd == "coco":
        run_coco(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else None)
    elif cmd == "screen":
        run_screen(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 100)
