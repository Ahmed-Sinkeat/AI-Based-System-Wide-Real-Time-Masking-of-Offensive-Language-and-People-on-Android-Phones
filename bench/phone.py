"""Phone-screen small-people test: synthetic 1080x2340 screens built from COCO photos, two layouts:
  feed  full-width posts (Instagram/Facebook home)      grid  3-column squares (Explore / search tab)
Runs the model on the whole screen (one 640 pass) and on 3 vertical tiles, measures who gets hidden,
and saves pictures of what the user would see + a sheet of the missed people at real size.

  python phone.py <ov-spec> [n_screens_per_layout]     e.g. ov-yolo:models/yolo26n-seg_int8_openvino_model/yolo26n-seg.xml:GPU
"""
import sys, json, random
from pathlib import Path
import numpy as np, cv2
from eval import make_predictor, regions, new_acc, accumulate, summarize, THRS, DATA

W, H = 1080, 2340
MM_PER_PX = 25.4 / 400        # typical phone ~400 ppi -> 1 px = 0.064 mm
VIZ_THR = 0.1                 # recall-first threshold proposed for v1
OUT = Path("results/phone"); OUT.mkdir(parents=True, exist_ok=True)


def paste(canvas, src, x0, y0):
    """Paste src at (x0, y0), clipped to the canvas. Works for images and masks."""
    h = min(src.shape[0], canvas.shape[0] - y0)
    if h > 0:
        canvas[y0:y0 + h, x0:x0 + src.shape[1]] = src[:h]


def place(coco, iid, x0, y0, w, h, cover):
    """Resize photo to w wide (feed) or to cover a w x h square (grid), centre-crop to w x h.
    Returns (image, [(mask, iscrowd)])."""
    img = cv2.imread(str(DATA / "val2017" / coco.loadImgs(iid)[0]["file_name"]))
    s = max(w / img.shape[1], h / img.shape[0]) if cover else w / img.shape[1]
    rw, rh = round(img.shape[1] * s), round(img.shape[0] * s)
    cx, cy = (rw - w) // 2, max(0, (rh - h) // 2)
    crop = lambda a, interp: cv2.resize(a, (rw, rh), interpolation=interp)[cy:cy + h, cx:cx + w]
    anns = coco.loadAnns(coco.getAnnIds(imgIds=iid, catIds=[1], iscrowd=None))
    return crop(img, cv2.INTER_AREA), [(crop(coco.annToMask(a), cv2.INTER_NEAREST) > 0, a["iscrowd"]) for a in anns]


def build(coco, ids, layout):
    canvas = np.full((H, W, 3), 250, np.uint8); canvas[:90] = 30
    placed, y, k = [], 90, 0
    if layout == "feed":
        while y < H and k < len(ids):
            cv2.circle(canvas, (60, y + 55), 35, (180, 180, 180), -1)
            cv2.putText(canvas, f"user_{ids[k] % 997}", (115, y + 68), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (20, 20, 20), 2)
            y += 110
            img, ms = place(coco, ids[k], 0, y, W, 1350, cover=False)
            placed.append((img, ms, 0, y)); y += img.shape[0]
            cv2.putText(canvas, "1,204 likes   nice caption text here", (20, min(H - 5, y + 60)),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (20, 20, 20), 2)
            y += 140; k += 1
    else:  # grid
        canvas[110:200, 30:W - 30] = 225; cv2.putText(canvas, "Search", (60, 170), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (120, 120, 120), 2)
        T, g, y = 358, 3, 220
        while y < H:
            for col in range(3):
                img, ms = place(coco, ids[k], 0, 0, T, T, cover=True)
                placed.append((img, ms, col * (T + g), y)); k += 1
            y += T + g
    inst, crowd = [], np.zeros((H, W), bool)
    for img, ms, x0, y0 in placed:
        paste(canvas, img, x0, y0)
        for m, iscrowd in ms:
            full = np.zeros((H, W), bool); paste(full, m, x0, y0)
            if iscrowd: crowd |= full
            elif full.any(): inst.append(full)
    return canvas, inst, crowd, k


def tiled(pred, canvas, n=3, ov=64):
    dets = []
    for i in range(n):
        ya, yb = max(0, i * H // n - ov), min(H, (i + 1) * H // n + ov)
        for s, m, b in pred(np.ascontiguousarray(canvas[ya:yb])):
            full = np.zeros((H, W), bool); full[ya:yb] = m
            dets.append((s, full, b + [0, ya, 0, ya]))
    return dets


def pixelate(img, region, block=24):
    small = cv2.resize(img, (W // block, H // block), interpolation=cv2.INTER_AREA)
    pix = cv2.resize(small, (W, H), interpolation=cv2.INTER_NEAREST)
    return np.where(region[..., None], pix, img)


def draw(canvas, inst, region, title):
    """What the user sees (blurred), plus each real person outlined: green hidden, orange partly, red missed."""
    v = pixelate(canvas, region)
    for m in inst:
        cov = (m & region).sum() / m.sum()
        col = (0, 200, 0) if cov >= 0.9 else (0, 150, 255) if cov >= 0.5 else (0, 0, 255)
        cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(v, cs, -1, col, 4)
        if cov < 0.9:
            ys, xs = np.nonzero(m)
            cv2.putText(v, f"{np.ptp(ys) + 1}px", (int(xs.min()), max(30, int(ys.min()) - 8)), cv2.FONT_HERSHEY_SIMPLEX, 1.0, col, 3)
    cv2.rectangle(v, (0, 0), (W, 90), (30, 30, 30), -1)
    cv2.putText(v, title, (20, 62), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 3)
    return v


def main(spec, n):
    from pycocotools.coco import COCO
    coco = COCO(str(DATA / "annotations/instances_val2017.json"))
    pos = sorted(coco.getImgIds(catIds=[1])); random.Random(7).shuffle(pos)
    pred = make_predictor(spec)
    report, missed = {}, []
    for layout in ("feed", "grid"):
        accs = {(v, t): new_acc() for v in ("full", "tiled3") for t in THRS}
        heights = {"full": {"hidden": [], "missed": []}, "tiled3": {"hidden": [], "missed": []}}
        cursor = 0 if layout == "feed" else 5000 % len(pos)
        for c in range(n):
            canvas, inst, crowd, used = build(coco, pos[cursor:] + pos[:cursor], layout); cursor = (cursor + used) % len(pos)
            areas = [int(m.sum()) for m in inst]
            res = {"full": pred(canvas), "tiled3": tiled(pred, canvas)}
            for v, dets in res.items():
                for t in THRS:
                    accumulate(accs[(v, t)], inst, areas, crowd, regions(dets, t, (H, W))["mask_dil"])
                reg = regions(dets, VIZ_THR, (H, W))["mask_dil"]
                for m in inst:
                    ys = np.nonzero(m)[0]; hgt = int(np.ptp(ys) + 1); cov = (m & reg).sum() / m.sum()
                    heights[v]["hidden" if cov >= 0.9 else "missed"].append(hgt)
                    if v == "full" and cov < 0.5 and len(missed) < 400:
                        x, y, w, h = cv2.boundingRect(m.astype(np.uint8)); missed.append((hgt, canvas[y:y + h, x:x + w].copy(), layout))
            if c < 3:
                regs = {v: regions(d, VIZ_THR, (H, W))["mask_dil"] for v, d in res.items()}
                pair = np.hstack([draw(canvas, inst, regs["full"], "whole screen, 1 pass"), np.full((H, 20, 3), 255, np.uint8),
                                  draw(canvas, inst, regs["tiled3"], "3 tiles")])
                cv2.imwrite(str(OUT / f"{layout}_{c}.jpg"), cv2.resize(pair, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 88])
            print(f"{layout} {c + 1}/{n}", flush=True)
        report[layout] = dict(screens=n, by_thr={f"{v}/{t}": summarize(a) for (v, t), a in accs.items()},
                              height_px={v: {k: (np.percentile(x, [10, 50, 90]).round().tolist() if x else None) for k, x in d.items()}
                                         for v, d in heights.items()})
    report["spec"], report["viz_threshold"], report["mm_per_px"] = spec, VIZ_THR, MM_PER_PX
    (OUT / f"phone__{spec.replace('/', '_').replace(':', '_')}.json").write_text(json.dumps(report, indent=1))
    # sheet: missed people, smallest first, at real screen size next to what the model gets (whole-screen pass)
    missed.sort(key=lambda r: r[0])
    pick = missed[::max(1, len(missed) // 24)][:24]
    cell, cells = 240, []
    for hgt, crop, layout in pick:
        a = np.full((cell, cell, 3), 255, np.uint8); s = min(1, (cell - 40) / max(crop.shape[:2]))
        cr = cv2.resize(crop, (max(1, round(crop.shape[1] * s)), max(1, round(crop.shape[0] * s))), interpolation=cv2.INTER_AREA); a[40:40 + cr.shape[0], :cr.shape[1]] = cr
        model_px = max(1, round(hgt * 640 / H))
        tiny = cv2.resize(crop, (max(1, round(crop.shape[1] * 640 / H)), model_px), interpolation=cv2.INTER_AREA)
        b = np.full((cell, cell, 3), 255, np.uint8); up = cell - 40
        tb = cv2.resize(tiny, (max(1, round(tiny.shape[1] * up / max(tiny.shape[:2]))), max(1, round(tiny.shape[0] * up / max(tiny.shape[:2])))), interpolation=cv2.INTER_NEAREST)
        b[40:40 + tb.shape[0], :tb.shape[1]] = tb
        cv2.putText(a, f"{hgt}px = {hgt * MM_PER_PX:.1f}mm", (4, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 200), 2)
        cv2.putText(b, f"model sees {model_px}px", (4, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 200), 2)
        cells.append(np.hstack([a, b, np.full((cell, 10, 3), 200, np.uint8)]))
    rows = [np.hstack(cells[i:i + 3] + [np.full((cell, cells[0].shape[1], 3), 255, np.uint8)] * (3 - len(cells[i:i + 3]))) for i in range(0, len(cells), 3)]
    if rows:
        cv2.imwrite(str(OUT / "missed_people_sheet.jpg"), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(json.dumps({l: {k: report[l]["by_thr"][k] for k in (f"full/{VIZ_THR}", f"tiled3/{VIZ_THR}")} | {"height_px": report[l]["height_px"]}
                      for l in ("feed", "grid")}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 60)
