"""
Pipeline Orchestrator — L1 → L2 → L3 → L4
完整执行编排，含 Loading 状态和错误处理。
"""
import asyncio, time, json, logging
from typing import Optional

logger = logging.getLogger("dualyield")

async def run_pipeline(user_params: dict) -> dict:
    """
    主入口 — 接收用户参数，返回完整渲染数据。

    user_params: {
        intent: "earn_yield" | "buy_dip" | "sell_high",
        underlying: "BTC" | "ETH" | "SOL",
        principal: float,
        durations: [7, 14],
        risk: "conservative" | "balanced" | "aggressive",
        target_price: float | None
    }
    """
    result = {"phase": "init", "error": None}

    try:
        # === Phase 0: Parse user context ===
        from .l2_compute.schema import UserContext, Intent, RiskLevel
        intent_map = {"earn_yield": Intent.EARN_YIELD, "buy_dip": Intent.BUY_DIP, "sell_high": Intent.SELL_HIGH}
        risk_map = {"conservative": RiskLevel.CONSERVATIVE, "balanced": RiskLevel.BALANCED, "aggressive": RiskLevel.AGGRESSIVE}
        ctx = UserContext(
            intent=intent_map.get(user_params.get("intent","earn_yield"), Intent.EARN_YIELD),
            underlying=user_params.get("underlying","BTC"),
            principal=user_params.get("principal", 10000),
            durations=user_params.get("durations", [7,14]),
            risk=risk_map.get(user_params.get("risk","balanced"), RiskLevel.BALANCED),
            target_price=user_params.get("target_price")
        )

        # === Phase 1: L1 Data Fetch ===
        result["phase"] = "l1_fetch"
        from .l1_data.fetcher import fetch_all
        products, market_data = await fetch_all([ctx.underlying])

        # === Phase 2: L2 Compute ===
        result["phase"] = "l2_compute"
        from .l2_compute.compute import run_l2
        # Load platform tiers from YAML
        import yaml, os
        meta_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "platform_meta.yaml")
        platform_tiers = {}
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                meta = yaml.safe_load(f)
            for p in meta.get("platforms", []):
                platform_tiers[p["id"]] = p.get("tier", 2)

        top3, ta = run_l2(products, market_data, ctx, platform_tiers)

        # === Phase 3: L3 Decision ===
        result["phase"] = "l3_decision"
        from .l3_decision.decision import call_llm
        ta_dict = {
            "current_price": ta.current_price, "ma20": ta.ma20, "ma60": ta.ma60,
            "ma120": ta.ma120, "rsi14": ta.rsi14, "macd_line": ta.macd_line,
            "macd_signal": ta.macd_signal, "macd_hist": ta.macd_hist,
            "hist_vol_annual": ta.hist_vol_annual, "trend": ta.trend,
            "sr_levels": [{"price":s.price,"strength":s.strength,"kind":s.kind} for s in ta.sr_levels]
        }
        top3_dicts = [p.__dict__ for p in top3]
        decision = await call_llm(
            user_ctx={"intent": ctx.intent.value, "principal": ctx.principal,
                      "durations": ctx.durations, "risk": ctx.risk.value},
            ta=ta_dict, top3=top3_dicts, all_count=len(top3)
        )

        # === Phase 4: Assemble render data ===
        result = {
            "phase": "done",
            "error": None,
            "user": {"intent": ctx.intent.value, "underlying": ctx.underlying,
                     "principal": ctx.principal, "risk": ctx.risk.value},
            "ta": ta_dict,
            "top3": top3_dicts,
            "decision": decision,
            "meta": {"generated_at": time.time(), "model": "dualyield-v2"}
        }

    except Exception as e:
        logger.error(f"Pipeline failed at {result.get('phase','unknown')}: {e}")
        result["error"] = str(e)

    return result
