#!/usr/bin/env bash
# Missing COCO evals, run while the timing stage is parked. Launched as `./reruns.sh gate-render.py`:
# the arg makes run_all.sh's `pgrep -f render.py` quiet-gate treat this as load, so timing never overlaps it.
source env.sh
kind() { case $1 in *rfdetr*) echo ov-rfdetr;; *) echo ov-yolo;; esac; }
for m in models/*/*.xml; do
  s="$(kind $m):$m:GPU"
  [ -f "results/coco__$(echo "$s" | tr '/:' '__').json" ] && continue
  for try in 1 2 3; do ../.venv/bin/python -u eval.py coco "$s" && break; echo "FAILED try $try $m"; done
done
echo RERUNS_DONE
