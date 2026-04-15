"""
L3 决策层 — LLM 调用 + 结果解析 + Fallback
"""
import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from pipeline.l2_compute.schema import ScoredProduct, UserContext, MarketStats

logger = logging.getLogger("yield-desk.l3")


# ═══════════════════════════════════════════════════
# Schema
# ═══════════════════════════════════════════════════

@dataclass
class BriefForCard:
    product_id: str
    one_liner: str


@dataclass
class DecisionOutput:
    headline: str = ""
    top1_reason: str = ""
    opportunity_cost: str = ""
    top2_reason: str = ""
    top3_reason: str = ""
    risk_warning: str = ""
    anomaly_alerts: list[str] = field(default_factory=list)
    brief_for_card: list[dict] = field(default_factory=list)


# ═══════════════════════════════════════════════════
# Prompt 加载
# ═══════════════════════════════════════════════════
PROMPT_PATH = Path(__file__).parent / "prompt.md"


def load_system_prompt() -> str:
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


# ═══════════════════════════════════════════════════
# LLM 调用
# ═══════════════════════════════════════════════════

# TODO: [TECH] API Key 从环境变量读取
ANTHROPIC_API_KEY = ""  # os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 1200
TEMPERATURE = 0.3
TIMEOUT_S = 20


async def call_llm(
    scored_products: list[ScoredProduct],
    ctx: UserContext,
    stats: MarketStats,
    weights: dict,
) -> DecisionOutput:
    """
    调用 LLM 生成决策输出。失败时走 fallback。
    """
    system = load_system_prompt()

    # 构建 user message — 只发 top 20
    user_data = {
        "user_context": asdict(ctx),
        "scored_products": [_product_to_llm_dict(p) for p in scored_products[:20]],
        "market_stats": asdict(stats),
        "weights_used": weights,
    }
    user_message = json.dumps(user_data, ensure_ascii=False, indent=2)

    try:
        result = await _invoke_anthropic(system, user_message)
        return _parse_output(result)
    except Exception as e:
        logger.error(f"L3 LLM failed: {e}, using fallback")
        return fallback_decision(scored_products, stats)


async def _invoke_anthropic(system: str, user_message: str) -> str:
    """
    调用 Anthropic Messages API。

    TODO: [TECH] 两种实现方式 (选一):
      方式 A — 使用 anthropic SDK:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        msg = await client.messages.create(
            model=MODEL, max_tokens=MAX_TOKENS, temperature=TEMPERATURE,
            system=system, messages=[{"role":"user","content":user_message}]
        )
        return msg.content[0].text

      方式 B — 使用 httpx 直接调:
        (见下面的实现)
    """
    import httpx

    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
    }
    body = {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "system": system,
        "messages": [{"role": "user", "content": user_message}],
    }

    async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
        resp = await client.post(url, json=body, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    # 提取文本
    text = ""
    for block in data.get("content", []):
        if block.get("type") == "text":
            text += block.get("text", "")
    return text.strip()


def _parse_output(raw_text: str) -> DecisionOutput:
    """
    解析 LLM 返回的 JSON 文本 → DecisionOutput。
    处理 markdown 代码块包裹等常见情况。
    """
    # 清理 markdown 代码块
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    data = json.loads(text)

    return DecisionOutput(
        headline=data.get("headline", ""),
        top1_reason=data.get("top1_reason", ""),
        opportunity_cost=data.get("opportunity_cost", ""),
        top2_reason=data.get("top2_reason", ""),
        top3_reason=data.get("top3_reason", ""),
        risk_warning=data.get("risk_warning", ""),
        anomaly_alerts=data.get("anomaly_alerts", []) or [],
        brief_for_card=data.get("brief_for_card", []) or [],
    )


# ═══════════════════════════════════════════════════
# Fallback — LLM 不可用时的模板输出
# ═══════════════════════════════════════════════════

def fallback_decision(
    scored_products: list[ScoredProduct],
    stats: MarketStats,
) -> DecisionOutput:
    """纯模板, 不调 LLM, 保证前端永远有内容。"""
    if not scored_products:
        return DecisionOutput(
            headline="当前条件下无匹配产品",
            risk_warning="请放宽安全或便利要求后重试。",
        )

    top = scored_products[0]
    delta = top.effective_apy - stats.avg_apy
    annual = top.effective_apy / 100

    cards = [
        {"product_id": p.source_id, "one_liner": f"{p.effective_apy:.1f}% · {p.yield_source}"}
        for p in scored_products[:5]
    ]

    alerts = []
    for p in scored_products[:3]:
        for flag in p.anomaly_flags:
            alerts.append(f"{p.platform_name}: {flag}")

    return DecisionOutput(
        headline=f"{top.platform_name} {top.product_name} 综合分 {top.composite_score} 居首",
        top1_reason=(
            f"{top.platform_name} 以综合分 {top.composite_score} 排名第一，"
            f"年化 {top.effective_apy:.1f}%，安全评分 {top.security_score:.0f}/100。"
            f"在 {stats.count} 个符合条件的产品中脱颖而出。"
        ),
        opportunity_cost=(
            f"比市场均值 {stats.avg_apy:.1f}% 高出 {delta:.1f} 个百分点，"
            f"$100K 本金年化多赚 ${delta * 1000:.0f}"
        ),
        top2_reason=(
            f"{scored_products[1].platform_name} 综合分 {scored_products[1].composite_score}"
            if len(scored_products) > 1 else "仅 1 个产品匹配"
        ),
        top3_reason=(
            f"{scored_products[2].platform_name} 综合分 {scored_products[2].composite_score}"
            if len(scored_products) > 2 else "不足 3 个产品匹配"
        ),
        risk_warning="CEX 存在对手方风险，DeFi 存在合约风险。请在投入资金前充分了解相关风险。",
        anomaly_alerts=alerts,
        brief_for_card=cards,
    )


# ═══════════════════════════════════════════════════
# Helper
# ═══════════════════════════════════════════════════

def _product_to_llm_dict(p: ScoredProduct) -> dict:
    """只发 LLM 需要的字段, 控制 token 用量。"""
    return {
        "source_id": p.source_id,
        "venue": p.venue,
        "platform_name": p.platform_name,
        "product_name": p.product_name,
        "asset_symbol": p.asset_symbol,
        "chain": p.chain,
        "tier": p.tier,
        "effective_apy": round(p.effective_apy, 2),
        "apy_30d_avg": round(p.apy_30d_avg, 2),
        "apy_30d_std": round(p.apy_30d_std, 2),
        "reward_dependency": round(p.reward_dependency, 2),
        "yield_source": p.yield_source,
        "product_type": p.product_type,
        "lock_days": p.lock_days,
        "redeem_delay_hours": p.redeem_delay_hours,
        "security_score": round(p.security_score, 1),
        "convenience_score": round(p.convenience_score, 1),
        "stability_score": round(p.stability_score, 1),
        "capacity_score": round(p.capacity_score, 1),
        "composite_score": p.composite_score,
        "rank": p.rank,
        "anomaly_flags": p.anomaly_flags,
        "tvl_usd": p.tvl_usd,
        "has_por": p.has_por,
        "has_insurance": p.has_insurance,
        "audits_count": len(p.audits) if isinstance(p.audits, list) else 0,
    }
