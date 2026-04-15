"""
L3 结论生成 — 模板优先，LLM 可选增强
v2 用模板即可，不需要 LLM 调用。
"""
import logging
from typing import Optional

logger = logging.getLogger("dualyield.l3")

RISK_LABELS = {"conservative": "保守", "balanced": "平衡", "aggressive": "激进"}
RISK_CAPS = {"conservative": "5%", "balanced": "15%", "aggressive": "30%"}


def render_conclusion(top1: dict, risk: str) -> str:
    """
    生成一句话结论 HTML。

    Args:
        top1: TOP 1 产品 dict，需含 platform/strike/apr/duration/prob/distance/side
        risk: "conservative" / "balanced" / "aggressive"

    Returns:
        HTML 字符串，包含 hl-* class 着色标记
    """
    if not top1:
        return "当前条件下未找到符合要求的档位，建议放宽风险偏好或增加期限。"

    rl = RISK_LABELS.get(risk, "平衡")
    rc = RISK_CAPS.get(risk, "15%")
    direction = "高于" if top1.get("side") == "sell" else "低于"

    strike = top1.get("strike", 0)
    strike_str = f"${strike:,}" if isinstance(strike, (int, float)) else f"${strike}"

    apr = top1.get("apr", 0)
    prob = top1.get("prob", 0)
    if isinstance(prob, float) and prob < 1:
        prob_pct = f"{prob * 100:.1f}"
    else:
        prob_pct = f"{prob:.1f}" if isinstance(prob, float) else str(prob)

    return (
        f'在{rl}策略下（到达概率 ≤ {rc}），'
        f'<strong>{top1.get("platform", "")}</strong> 的 '
        f'<span class="hl-blue">{strike_str}</span> 档位表现最优：'
        f'年化 <span class="hl-green">{apr}%</span>，'
        f'{top1.get("duration", 0)}天内触达概率仅 '
        f'<span class="hl-yellow">{prob_pct}%</span>。'
        f'该价位{direction}当前价 {top1.get("distance", 0)}%。'
    )


def render_conclusion_plain(top1: dict, risk: str) -> str:
    """纯文本版本（用于日志或 API 输出）"""
    if not top1:
        return "未找到符合条件的档位。"

    rl = RISK_LABELS.get(risk, "平衡")
    rc = RISK_CAPS.get(risk, "15%")
    direction = "高于" if top1.get("side") == "sell" else "低于"

    return (
        f"在{rl}策略下（到达概率 ≤ {rc}），"
        f"{top1.get('platform', '')} 的 ${top1.get('strike', 0):,} 档位表现最优："
        f"年化 {top1.get('apr', 0)}%，"
        f"{top1.get('duration', 0)}天内触达概率仅 "
        f"{top1.get('prob', 0) * 100:.1f}%。"
        f"该价位{direction}当前价 {top1.get('distance', 0)}%。"
    )


async def call_llm(user_ctx: dict, ta: dict, top3: list, all_count: int) -> dict:
    """Template-mode compatibility wrapper for the orchestrator."""
    top1 = top3[0] if top3 else {}
    normalized = {
        "platform": top1.get("platform", ""),
        "strike": top1.get("strike", 0),
        "apr": top1.get("apr", 0),
        "duration": top1.get("duration_days", top1.get("duration", 0)),
        "prob": top1.get("touch_prob", top1.get("prob", 0)),
        "distance": round(top1.get("distance_pct", 0) * 100, 1) if "distance_pct" in top1 else top1.get("distance", 0),
        "side": "sell" if top1.get("side") in ["sell_high", "sell"] else "buy",
    }
    risk = user_ctx.get("risk", "balanced")
    return {
        "mode": "template",
        "html": render_conclusion(normalized, risk),
        "plain": render_conclusion_plain(normalized, risk),
        "count": all_count,
    }
