#!/usr/bin/env bash
# All timing measurements, only on a quiet machine. Quiet = no render.py / reruns for 3 checks in a row (90 s),
# because the other session's render queue has short gaps between jobs that a single check slips through.
source env.sh; export PATH=$PWD/../.venv/bin:$PATH
PY="python -u"
kind() { case $1 in *rfdetr*) echo ov-rfdetr;; *) echo ov-yolo;; esac; }
busy() { pgrep -f 'render.py|reruns.sh' >/dev/null; }
wait_quiet() { local ok=0 t=0; while [ $ok -lt 3 ]; do if busy; then ok=0; else ok=$((ok+1)); fi; sleep 30; t=$((t+30)); done; echo "quiet after ${t}s"; }
retry() { for try in 1 2 3; do "$@" && return 0; echo "FAILED try $try: $*"; done; }

wait_quiet
rm -f results/latency.csv; $PY latency.py
for m in models/*/*.xml; do busy && wait_quiet; retry $PY runtime.py "$(kind $m):$m:GPU" 30; done
for m in models/yolo26n-seg_int8*/*.xml models/yolo11n-seg_int8*/*.xml models/rfdetrsegnano_int8/*.xml; do
  busy && wait_quiet; retry $PY runtime.py "$(kind $m):$m:CPU" 30
done
busy && wait_quiet; $PY readback.py && echo READBACK_DONE
busy && echo "WARNING: load appeared during timing run"
python summarize.py > /dev/null && echo TIMING_DONE
