# Yield Desk · Handoff Review

## Verdict

这是一个 **质量不错的半成品 PM→Engineering handoff package**。

它的价值不在于“已经做完”，而在于：
- 架构已经清楚
- L2 算法主体已经成型
- 前端原型已经能表达产品 intent
- 技术待办已经被明确列出

## What is already good

- 4-layer pipeline 拆分清晰
- `RawProduct / ScoredProduct / UserContext / MarketStats` schema 明确
- L2 过滤 / enrich / derive / score / rank / anomaly detect 已经基本成型
- 静态元数据足够支持评分模型继续推进
- LLM 挂掉时有 fallback
- 前端 `implementation/frontend/yield-desk.html` 是很好的高保真产品原型
- 当前 `implementation/tests/test_l2_scorer.py` 可通过（16/16）

## Main engineering gaps

### 1. L1 not production complete
- Antseer 主通道契约未锁定
- DefiLlama + Binance 之外，多数 CEX 仍是 stub
- 各家签名 / key / normalize 还没补齐

### 2. L2 still has known simplifications
- 阶梯利率解析仍是简化版
- 手续费解析仍是简化版
- Pendle 动态 lock_days 未实现

### 3. L3 not deployment-ready
- 真实 API key / env wiring 未完成
- Prompt 有基础，但还没完成调优闭环

### 4. L4 still mock-only
- 前端仍是 mock 数据
- 真实数据灌注路径还未锁定

### 5. Reliability layer missing
- 无 L1 fixtures
- 无 E2E pipeline test
- retry/cache/rate-limit 还主要停留在设计层

## Known issue fixed in this shared package

- `implementation/pipeline/l1_data/fetcher.py` 的 Antseer dict → `RawProduct` 映射方式已做最小修正，避免 `hasattr(RawProduct, k)` 带来的字段过滤错误。
- 但这不代表 Antseer 路径已完成，真实接口字段仍需工程确认。

## Suggested next owners

- **Backend engineer**: L1 connectors + config/env + orchestration hardening
- **Frontend engineer**: mock → real data injection + responsive adaptation
- **PM / design**: prompt tuning, anomaly copy quality, edge-case acceptance

## Share note

把这个包分享给技术同事时，建议直接说明：

> 这是一个“产品定义已经完成、工程还没收尾”的 skill 包。
> 请优先看 `docs/review/HANDOFF-REVIEW.md` 和 `docs/handoff/TODO-TECH.md`，不要默认它已经能直接上线。
