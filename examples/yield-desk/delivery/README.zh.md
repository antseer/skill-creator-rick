# Yield Desk

已迁移到 vNext `docs / implementation / delivery` 标准的稳定币收益决策示例包。

## 阅读顺序
1. `docs/product/PRD.md`
2. `docs/handoff/TODO-TECH.md`
3. `docs/review/HANDOFF-REVIEW.md`
4. `implementation/pipeline/`

## 快速开始
```bash
pip install -r requirements.txt
python -m pytest implementation/tests/test_l2_scorer.py
python -m implementation.pipeline.orchestrator
```
