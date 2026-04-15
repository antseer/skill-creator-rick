"""
Pipeline 编排器 — L1 → L2 → L3 → L4

L4 由前端 HTML 负责, 本模块输出 L2+L3 的结构化数据供前端消费。
"""
import asyncio
import logging
import time
from dataclasses import asdict
from typing import Optional

from implementation.pipeline.l1_data.fetcher import fetch_all_products, fetch_pool_history
from implementation.pipeline.l2_compute.compute import run_l2, get_weights
from implementation.pipeline.l2_compute.schema import UserContext, ScoredProduct, MarketStats
from implementation.pipeline.l3_decision.decision import call_llm, fallback_decision, DecisionOutput

logger = logging.getLogger("yield-desk")
logging.basicConfig(level=logging.INFO)


async def run_pipeline(ctx: UserContext) -> dict:
    """
    完整 Pipeline 执行。

    返回:
    {
      "status": "ok" | "partial" | "error",
      "elapsed_ms": int,
      "scored_products": [...],   # ScoredProduct[] as dicts
      "market_stats": {...},
      "decision": {...},          # DecisionOutput as dict
      "weights_used": {...},
      "warnings": [str],
    }
    """
    t0 = time.time()
    warnings = []

    # ═══════════ L1: 数据获取 ═══════════
    logger.info("L1: Fetching products...")
    try:
        raw_products = await fetch_all_products(ctx.assets, ctx.venues)
    except Exception as e:
        logger.error(f"L1 fatal: {e}")
        return _error_result(f"数据获取失败: {e}", t0)

    if not raw_products:
        return _error_result("无数据返回，请检查网络或 API Key", t0)

    logger.info(f"L1 done: {len(raw_products)} raw products")

    # ── 拉历史 (DeFi only, 并发, 可选) ──
    history_map = {}
    defi_products = [p for p in raw_products if p.source_api == "defillama"]
    if defi_products:
        # 只拉 top 50 按 tvl 排序的池历史, 避免过多请求
        defi_products.sort(key=lambda p: p.tvl_usd, reverse=True)
        top_pools = defi_products[:50]

        async def _fetch_hist(p):
            h = await fetch_pool_history(p.source_api, p.source_id, 30)
            return p.source_id, h

        try:
            results = await asyncio.gather(
                *[_fetch_hist(p) for p in top_pools],
                return_exceptions=True,
            )
            for r in results:
                if isinstance(r, tuple):
                    history_map[r[0]] = r[1]
        except Exception as e:
            warnings.append(f"部分历史数据获取失败: {e}")

    # ═══════════ L2: 计算评分 ═══════════
    logger.info("L2: Computing scores...")
    scored_products, market_stats = run_l2(raw_products, ctx, history_map)

    if not scored_products:
        return _error_result("筛选后无匹配产品，请放宽条件", t0)

    weights = get_weights(ctx)

    # ═══════════ L3: 决策推理 ═══════════
    logger.info("L3: Calling LLM for decision...")
    try:
        decision = await call_llm(scored_products, ctx, market_stats, weights)
    except Exception as e:
        logger.warning(f"L3 LLM failed: {e}, using fallback")
        decision = fallback_decision(scored_products, market_stats)
        warnings.append("LLM 不可用，使用模板输出")

    # ═══════════ 组装结果 ═══════════
    elapsed = round((time.time() - t0) * 1000)
    logger.info(f"Pipeline done in {elapsed}ms")

    return {
        "status": "ok" if not warnings else "partial",
        "elapsed_ms": elapsed,
        "scored_products": [asdict(p) for p in scored_products],
        "market_stats": asdict(market_stats),
        "decision": asdict(decision),
        "weights_used": weights,
        "warnings": warnings,
    }


def _error_result(msg: str, t0: float) -> dict:
    return {
        "status": "error",
        "elapsed_ms": round((time.time() - t0) * 1000),
        "scored_products": [],
        "market_stats": {},
        "decision": asdict(DecisionOutput(headline=msg, risk_warning=msg)),
        "weights_used": {},
        "warnings": [msg],
    }


# ═══════════════════════════════════════════════════
# CLI 入口 (开发调试用)
# ═══════════════════════════════════════════════════
if __name__ == "__main__":
    import json

    ctx = UserContext(
        assets=["USDC"],
        venues=["CEX", "DeFi"],
        amount=100000,
        sec_priority="balanced",
        conv_priority="balanced",
        kyc="basic",
    )

    result = asyncio.run(run_pipeline(ctx))
    print(json.dumps(result, ensure_ascii=False, indent=2))
