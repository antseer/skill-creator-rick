# DualYield

Dual-investment recommendation example migrated to the vNext `docs / implementation / delivery` package standard.

## Read order
1. `docs/product/PRD.md`
2. `docs/handoff/TODO-TECH.md`
3. `docs/review/HANDOFF-REVIEW.md`
4. `implementation/pipeline/`

## Quick start
```bash
python3 -m unittest implementation.tests.test_l2 -v
```

Optional smoke test:
```bash
python3 - <<'PY'
import asyncio, sys
sys.path.insert(0, '.')
from implementation.pipeline.orchestrator import run_pipeline
print(asyncio.run(run_pipeline({"intent":"earn_yield","underlying":"BTC","principal":10000,"durations":[7,14],"risk":"balanced"})))
PY
```
