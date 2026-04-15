# Yield Desk

Stablecoin yield decision example migrated to the vNext `docs / implementation / delivery` package standard.

## Read order
1. `docs/product/PRD.md`
2. `docs/handoff/TODO-TECH.md`
3. `docs/review/HANDOFF-REVIEW.md`
4. `implementation/pipeline/`

## Quick start
```bash
pip install -r requirements.txt
python -m pytest implementation/tests/test_l2_scorer.py
python -m implementation.pipeline.orchestrator
```
