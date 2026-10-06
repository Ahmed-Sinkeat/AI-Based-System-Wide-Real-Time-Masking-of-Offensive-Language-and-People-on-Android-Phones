#!/usr/bin/env bash
# clean re-run: all daemon-loop timings, then the CPU INT8 RF-DETR accuracy eval (accuracy last, so it can't skew timing)
source env.sh
./run_runtime.sh
../.venv/bin/python -u eval.py coco ov-rfdetr:models/rfdetrsegnano_int8/model.xml:CPU && echo CPU_INT8_DONE
../.venv/bin/python summarize.py >/dev/null && echo FINAL_DONE
