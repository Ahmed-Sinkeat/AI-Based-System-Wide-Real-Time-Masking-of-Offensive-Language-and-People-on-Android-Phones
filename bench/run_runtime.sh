#!/usr/bin/env bash
source env.sh; PY="../.venv/bin/python -u"
kind() { case $1 in *rfdetr*) echo ov-rfdetr;; *) echo ov-yolo;; esac; }
retry() { for try in 1 2 3; do "$@" && return 0; echo "FAILED try $try: $*"; done; }
for m in models/*/*.xml; do retry $PY runtime.py "$(kind $m):$m:GPU" 30; done
for m in models/yolo26n-seg_int8*/*.xml models/yolo11n-seg_int8*/*.xml models/rfdetrsegnano_int8/*.xml; do retry $PY runtime.py "$(kind $m):$m:CPU" 30; done
../.venv/bin/python summarize.py >/dev/null; echo RUNTIME_DONE
