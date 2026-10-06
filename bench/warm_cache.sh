#!/usr/bin/env bash
# Pre-compile every model for GPU into ovcache/ (retry: IGC crashes on ~1 in 3 cold compiles here).
# Once cached, later loads skip IGC entirely. A real daemon should ship these blobs the same way.
source env.sh
for m in models/*/*.xml; do
  for try in 1 2 3 4 5 6; do
    ../.venv/bin/python -c "
import openvino as ov; c=ov.Core(); c.set_property({'CACHE_DIR':'ovcache'})
c.compile_model('$m','GPU',{'PERFORMANCE_HINT':'LATENCY'})" >/dev/null 2>&1 && { echo "cached $m (try $try)"; break; }
  done
done
