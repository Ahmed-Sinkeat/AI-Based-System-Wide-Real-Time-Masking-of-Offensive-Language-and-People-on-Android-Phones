#!/usr/bin/env bash
# Full P0 measurement run. Accuracy first (unaffected by load), timing only once the machine is quiet.
set -u
source env.sh; export PATH=$PWD/../.venv/bin:$PATH
PY="python -u"
kind() { case $1 in *rfdetr*) echo ov-rfdetr;; *) echo ov-yolo;; esac; }
wait_quiet() {  # wait (max 6h) until no other render job is using the iGPU/CPU
  local t=0
  while pgrep -f "render.py" >/dev/null && [ $t -lt 21600 ]; do sleep 30; t=$((t+30)); done
  sleep 20; echo "quiet-wait ${t}s, contended=$(pgrep -f render.py >/dev/null && echo yes || echo no)"
}

$PY quant_rfdetr.py || echo "FAILED quant"
for m in models/*/*.xml; do
  [ -f "results/coco__$(echo "$(kind $m):$m:GPU" | tr '/:' '__').json" ] && continue
  $PY eval.py coco "$(kind $m):$m:GPU" || echo "FAILED coco $m"
done
for m in models/yolo11n-seg_fp16*/*.xml models/yolo26n-seg_fp16*/*.xml models/yolo11s-seg_fp16*/*.xml models/rfdetrsegnano_fp16/*.xml models/rfdetrsegsmall_fp16/*.xml; do
  $PY eval.py screen "$(kind $m):$m:GPU" 100 || echo "FAILED screen $m"
done

wait_quiet
rm -f results/latency.csv; $PY latency.py
for m in models/*/*.xml; do
  pgrep -f render.py >/dev/null && wait_quiet
  $PY runtime.py "$(kind $m):$m:GPU" 30 || echo "FAILED runtime $m"
done
$PY runtime.py "ov-yolo:$(ls models/yolo26n-seg_int8*/*.xml):CPU" 30
$PY runtime.py "ov-yolo:$(ls models/yolo11n-seg_int8*/*.xml):CPU" 30
echo ALL_DONE
