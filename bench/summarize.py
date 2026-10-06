"""results/*.json + latency.csv -> results/SUMMARY.md (markdown tables)."""
import json, csv, re
from pathlib import Path

R = Path("results")
name = lambda s: re.sub(r"_openvino_model|_model\.xml|\.xml|models_|ov-(yolo|rfdetr)_", "", s)
short = lambda spec: name(spec.split(":")[1].split("/")[1]) + ("" if spec.endswith("GPU") else " (CPU)")
pct = lambda x: "–" if x is None else f"{100 * x:.1f}"
f1 = lambda x: "–" if x is None else f"{x:.1f}"
out = []

if (R / "latency.csv").exists():
    out += ["## Raw model latency (OpenVINO benchmark_app, batch 1, latency hint)", "",
            "| model | input | GPU median ms | GPU FPS | CPU median ms | CPU FPS | GPU compile ms | contended |", "|---|---|---|---|---|---|---|---|"]
    rows = {}
    for r in csv.DictReader(open(R / "latency.csv")):
        rows.setdefault(r["model"], {})[r["device"]] = r
    for m, d in sorted(rows.items()):
        g, c = d.get("GPU", {}), d.get("CPU", {})
        out.append(f"| {name(m)} | {(lambda s: 'fail' if s.startswith('FAILED') else s)((g or c).get('input',''))} | {g.get('median_ms') or 'fail'} | {g.get('fps','')} | "
                   f"{c.get('median_ms') or 'fail'} | {c.get('fps','')} | {g.get('compile_ms','')} | {g.get('contended','')} |")
    out.append("")

rt = sorted(R.glob("runtime__*.json"))
if rt:
    out += ["## Daemon loop (640x360 frame in, masks out, conf 0.25)", "",
            "| model | p50 ms | p95 ms | p99 ms | FPS | CPU % (1 core=100) | RSS MB | GPU MHz | contended |", "|---|---|---|---|---|---|---|---|---|"]
    for p in rt:
        d = json.loads(p.read_text())
        out.append(f"| {short(d['spec'])} | {f1(d['p50_ms'])} | {f1(d['p95_ms'])} | {f1(d['p99_ms'])} | {f1(d['fps'])} | "
                   f"{f1(d['proc_cpu_pct_of_one_core'])} | {d['rss_mb']:.0f} | {d['gpu_mhz_median']} | {d['contended']} |")
    out.append("")

coco = sorted(R.glob("coco__*GPU.json"))
if coco:
    out += ["## COCO val2017 person accuracy (2693 person images + 500 person-free)", "",
            "Instance \"hidden\" = ≥90% of its pixels under the blur region. Region = dilated mask (~1% of long side).", ""]
    for thr in ("0.25", "0.1"):
        out += [f"### threshold {thr}", "",
                "| model | mask AP | AP small | AP large | hidden small | hidden medium | hidden large | pixel recall | over-blur | false alarm on person-free imgs |",
                "|---|---|---|---|---|---|---|---|---|---|"]
        for p in coco:
            d = json.loads(p.read_text()); a = d["person_mask_ap"]; s = d["by_thr"][f"{thr}/mask_dil"]
            out.append(f"| {short(d['spec'])} | {a['AP']:.3f} | {a['AP_small']:.3f} | {a['AP_large']:.3f} | {pct(s['small']['rec90'])} | "
                       f"{pct(s['medium']['rec90'])} | {pct(s['large']['rec90'])} | {pct(s['pixel_recall'])} | {pct(s['overblur'])} | "
                       f"{pct(s.get('neg_false_alarm_rate'))} |")
        out.append("")
    out += ["### render mode comparison at threshold 0.25 (hidden %, small/medium/large, pixel recall, over-blur)", "",
            "| model | raw mask | dilated mask | boxes |", "|---|---|---|---|"]
    for p in coco:
        d = json.loads(p.read_text())
        cell = lambda m: (lambda s: f"{pct(s['small']['rec90'])}/{pct(s['medium']['rec90'])}/{pct(s['large']['rec90'])}, "
                          f"px {pct(s['pixel_recall'])}, over {pct(s['overblur'])}")(d["by_thr"][f"0.25/{m}"])
        out.append(f"| {short(d['spec'])} | {cell('mask')} | {cell('mask_dil')} | {cell('box')} |")
    out.append("")

scr = sorted(R.glob("screen__*.json"))
if scr:
    out += ["## Synthetic 1920x1080 feed window (6 COCO photos as tiles), threshold 0.25, dilated mask", "",
            "| model | pass | hidden small | hidden medium | hidden large | pixel recall | over-blur | e2e ms (python, unoptimized) |", "|---|---|---|---|---|---|---|---|"]
    for p in scr:
        d = json.loads(p.read_text())
        for v in ("full", "tiled2x2"):
            s = d["by_thr"][f"{v}/0.25"]
            out.append(f"| {short(d['spec'])} | {v} | {pct(s['small']['rec90'])} (n={s['small']['n']}) | {pct(s['medium']['rec90'])} | "
                       f"{pct(s['large']['rec90'])} | {pct(s['pixel_recall'])} | {pct(s['overblur'])} | {f1(d['e2e_ms_median'][v])} |")
    out.append("")

if (R / "readback.json").exists():
    d = json.loads((R / "readback.json").read_text())
    out += ["## Compositor-side GPU cost (headless EGL, Mesa iris)", "", "| step | p50 ms | p95 ms | max ms |", "|---|---|---|---|"]
    for k, v in d.items():
        if isinstance(v, dict):
            out.append(f"| {k} | {v['p50']:.2f} | {v['p95']:.2f} | {v['max']:.2f} |")
    out += ["", f"contended: {d['contended']}", ""]

(R / "SUMMARY.md").write_text("\n".join(out))
print("\n".join(out))
