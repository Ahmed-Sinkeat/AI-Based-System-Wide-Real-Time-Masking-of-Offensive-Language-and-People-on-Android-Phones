#!/usr/bin/env bash
# after run_all.sh: (re)run every missing result with retries (IGC, the Intel GPU kernel compiler, crashes
# intermittently while compiling; compiled kernels are cached in ovcache/ so a retry usually passes),
# then the compositor-side readback bench on a quiet machine, then the summary.
source env.sh
PY="../.venv/bin/python -u"
until grep -q ALL_DONE results/run_all.log; do sleep 30; done
kind() { case $1 in *rfdetr*) echo ov-rfdetr;; *) echo ov-yolo;; esac; }
has() { [ -f "results/$1__$(echo "$2" | tr '/:' '__').json" ]; }
retry() { for try in 1 2 3; do "$@" && return 0; echo "FAILED try $try: $*"; done; }
for m in models/*/*.xml; do
  s="$(kind $m):$m:GPU"; has coco "$s" || retry $PY eval.py coco "$s"
done
for m in models/yolo11n-seg_fp16*/*.xml models/yolo26n-seg_fp16*/*.xml models/yolo11s-seg_fp16*/*.xml models/rfdetrsegnano_fp16/*.xml models/rfdetrsegsmall_fp16/*.xml; do
  s="$(kind $m):$m:GPU"; has screen "$s" || retry $PY eval.py screen "$s" 100
done
while pgrep -f render.py >/dev/null; do sleep 30; done; sleep 20
for m in models/*/*.xml; do
  s="$(kind $m):$m:GPU"; has runtime "$s" || retry $PY runtime.py "$s" 30
done
$PY readback.py && echo READBACK_DONE
../.venv/bin/python summarize.py > /dev/null && echo SUMMARY_DONE
