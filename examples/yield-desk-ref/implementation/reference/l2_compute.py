"""
L2 计算层 — 完整 Pipeline
filter → enrich → derive → score → rank → anomaly_detect

所有函数都是纯计算、确定性的，不调 LLM、不调网络。
"""
import math
import yaml
import logging
from statistics import mean, stdev
from pathlib import Path
from typing import Optional

from pipeline.l1_data.schema import RawProduct
from pipeline.l2_compute.schema import ScoredProduct, UserContext, MarketStats

logger = logging.getLogger("yield-desk.l2")

# ═══════════════════════════════════════════════════
# 加载静态安全元数据
# ═══════════════════════════════════════════════════
DATA_DIR = Path(__file__).parent.parent.parent / "data"


def _load_meta() -> dict:
    """加载 platform_meta.yaml + protocol_meta.yaml, 合并为 {slug: {...}}。"""
    merged = {}
    for fname in ["platform_meta.yaml", "protocol_meta.yaml"]:
        path = DATA_DIR / fname
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                merged.update(data)
    return merged


META = {}  # 延迟加载

def get_meta() -> dict:
    global META
    if not META:
        META = _load_meta()
    return META


# ═══════════════════════════════════════════════════
# 权重矩阵
# ═══════════════════════════════════════════════════
WEIGHT_MATRIX = {
    # (sec_priority, conv_priority): {apy, sec, conv, cap, stab}
    ("balanced", "balanced"): {"apy": 0.35, "sec": 0.25, "conv": 0.20, "cap": 0.10, "stab": 0.10},
    ("tier1",    "balanced"): {"apy": 0.25, "sec": 0.40, "conv": 0.15, "cap": 0.10, "stab": 0.10},
    ("loose",    "balanced"): {"apy": 0.45, "sec": 0.15, "conv": 0.20, "cap": 0.10, "stab": 0.10},
    ("balanced", "flex"):     {"apy": 0.30, "sec": 0.25, "conv": 0.25, "cap": 0.10, "stab": 0.10},
    ("balanced", "any"):      {"apy": 0.40, "sec": 0.25, "conv": 0.15, "cap": 0.10, "stab": 0.10},
    ("tier1",    "flex"):     {"apy": 0.20, "sec": 0.35, "conv": 0.25, "cap": 0.10, "stab": 0.10},
    ("loose",    "any"):      {"apy": 0.50, "sec": 0.10, "conv": 0.15, "cap": 0.10, "stab": 0.15},
    ("tier1",    "any"):      {"apy": 0.25, "sec": 0.40, "conv": 0.10, "cap": 0.10, "stab": 0.15},
    ("loose",    "flex"):     {"apy": 0.40, "sec": 0.12, "conv": 0.28, "cap": 0.10, "stab": 0.10},
}


def get_weights(ctx: UserContext) -> dict:
    key = (ctx.sec_priority, ctx.conv_priority)
    return WEIGHT_MATRIX.get(key, WEIGHT_MATRIX[("balanced", "balanced")])


# ═══════════════════════════════════════════════════
# Step 1: 过滤
# ═══════════════════════════════════════════════════
def filter_products(products: list[RawProduct], ctx: UserContext) -> list[RawProduct]:
    """按用户参数过滤产品。"""
    out = []
    for p in products:
        if not p.available or p.is_sold_out:
            continue
        if p.apy_total <= 0 or p.apy_total > 200:
            continue
        if p.asset_symbol not in ctx.assets:
            continue
        if p.venue not in ctx.venues:
            continue

        # 便利性过滤
        if ctx.conv_priority == "flex" and p.lock_days > 0:
            continue
        if ctx.conv_priority == "balanced" and p.lock_days > 30:
            continue

        # DeFi: TVL 过低
        if p.venue == "DeFi" and p.tvl_usd < 100_000:
            continue

        # 仅单一资产暴露
        if p.exposure == "multi":
            continue

        out.append(p)

    # 兜底: 如果过滤后为空, 放宽安全限制重试一次
    if not out and products:
        logger.warning("Filter returned 0 products, relaxing constraints")
        return [p for p in products if p.available and not p.is_sold_out
                and 0 < p.apy_total <= 200
                and p.asset_symbol in ctx.assets and p.venue in ctx.venues]

    return out


# ═══════════════════════════════════════════════════
# Step 2: 补全安全元数据
# ═══════════════════════════════════════════════════
def enrich(product: RawProduct) -> ScoredProduct:
    """
    RawProduct → ScoredProduct, 从 YAML 补全安全元数据。
    """
    meta = get_meta()
    pm = meta.get(product.platform_slug, {})

    sp = ScoredProduct(**{k: getattr(product, k) for k in product.__dataclass_fields__})
    sp.tier = pm.get("tier", 3)
    sp.audits = pm.get("audits", [])
    sp.has_insurance = pm.get("has_insurance", False)
    sp.has_por = pm.get("has_por", False)
    sp.last_por_at = pm.get("last_por_at")
    sp.incident_history = pm.get("incident_history", [])
    sp.kyc_level = pm.get("kyc_level", 0)
    sp.restricted_regions = pm.get("restricted_regions", [])
    sp.contract_upgradeable = pm.get("contract_upgradeable")
    sp.multisig_signers = pm.get("multisig_signers")
    sp.site_url = pm.get("site_url", "")
    sp.yield_source = pm.get("yield_source", product.pool_meta or "")
    sp.redeem_delay_hours = pm.get("redeem_delay_hours", 0.1 if product.product_type == "flexible" else 0)
    sp.fees = pm.get("fees", {})

    return sp


# ═══════════════════════════════════════════════════
# Step 3: 计算派生字段
# ═══════════════════════════════════════════════════
def derive(sp: ScoredProduct, history: list[float], ctx: UserContext) -> ScoredProduct:
    """计算 30 日统计、收益稀释、有效利率等。"""

    # ── 30 日 APY 统计 ──
    if history and len(history) >= 7:
        recent = history[-30:] if len(history) >= 30 else history
        sp.apy_30d_avg = mean(recent)
        sp.apy_30d_std = stdev(recent) if len(recent) >= 2 else 0
        sp.apy_7d_trend = history[-1] - history[-7] if len(history) >= 7 else 0
    else:
        sp.apy_30d_avg = sp.apy_total
        sp.apy_30d_std = 0
        sp.apy_7d_trend = 0

    # ── 收益稀释风险 ──
    if sp.apy_reward and sp.apy_reward > 0:
        sp.apy_without_reward = sp.apy_base or (sp.apy_total - sp.apy_reward)
        sp.reward_dependency = sp.apy_reward / max(sp.apy_total, 0.01)
    else:
        sp.apy_without_reward = sp.apy_total
        sp.reward_dependency = 0

    # ── 阶梯利率 (CEX 特有) ──
    if sp.apr_tiers:
        sp.effective_apy = _find_tier_rate(sp.apr_tiers, ctx.amount)
    else:
        sp.effective_apy = sp.apy_total

    # ── 安全分 ──
    sp.security_score = _calc_security_score(sp)

    # ── 便利性分 ──
    sp.convenience_score = _calc_convenience_score(sp)

    # ── 稳定性分 ──
    sp.stability_score = _calc_stability_score(sp)

    # ── 容量分 ──
    sp.capacity_score = _calc_capacity_score(sp, ctx.amount)

    return sp


# ═══════════════════════════════════════════════════
# Step 4+5: 归一化 + 加权评分
# ═══════════════════════════════════════════════════
def score(sp: ScoredProduct, ctx: UserContext) -> ScoredProduct:
    """计算综合分。"""
    w = get_weights(ctx)

    dims = {
        "apy":  _norm(sp.effective_apy, 0, 15),
        "sec":  _norm(sp.security_score, 0, 100),
        "conv": _norm(sp.convenience_score, 0, 100),
        "cap":  _norm(sp.capacity_score, 0, 100),
        "stab": _norm(sp.stability_score, 0, 100),
    }

    sp.radar = dims.copy()
    sp.composite_score = round(100 * sum(dims[k] * w[k] for k in dims))
    return sp


# ═══════════════════════════════════════════════════
# Step 6: 排序
# ═══════════════════════════════════════════════════
def rank(products: list[ScoredProduct]) -> list[ScoredProduct]:
    products.sort(key=lambda p: (-p.composite_score, -p.security_score, -p.effective_apy))
    for i, p in enumerate(products):
        p.rank = i + 1
    return products


# ═══════════════════════════════════════════════════
# Step 7: 异常检测
# ═══════════════════════════════════════════════════
def detect_anomalies(products: list[ScoredProduct]) -> list[ScoredProduct]:
    if not products:
        return products

    apys = [p.effective_apy for p in products]
    sorted_apys = sorted(apys)
    median_apy = sorted_apys[len(sorted_apys) // 2]

    for p in products:
        p.anomaly_flags = []

        if p.effective_apy > median_apy * 3 and p.effective_apy > 10:
            p.anomaly_flags.append("APY_OUTLIER")

        if p.apy_7d_trend < -2:
            p.anomaly_flags.append("APY_DECLINING")

        if p.reward_dependency > 0.7:
            p.anomaly_flags.append("HIGH_REWARD_DEPENDENCY")

        if p.remaining_capacity and p.remaining_capacity < 1_000_000:
            p.anomaly_flags.append("LOW_CAPACITY")

    return products


# ═══════════════════════════════════════════════════
# 市场统计
# ═══════════════════════════════════════════════════
def calc_market_stats(products: list[ScoredProduct]) -> MarketStats:
    if not products:
        return MarketStats()
    apys = [p.effective_apy for p in products]
    sorted_apys = sorted(apys)
    return MarketStats(
        avg_apy=round(mean(apys), 2),
        median_apy=round(sorted_apys[len(sorted_apys) // 2], 2),
        count=len(products),
    )


# ═══════════════════════════════════════════════════
# 内部: 评分函数 (PRD §2.4)
# ═══════════════════════════════════════════════════

def _calc_security_score(p: ScoredProduct) -> float:
    score = 0

    # 平台基础分 (最高 40)
    if p.venue == "CEX":
        score += {1: 40, 2: 25, 3: 12}.get(p.tier, 12)
    else:
        score += {1: 38, 2: 22, 3: 10}.get(p.tier, 10)

    # 审计加分 (最高 25)
    n_audits = len(p.audits) if isinstance(p.audits, list) else 0
    score += min(n_audits * 8, 25)

    # 储备金/保险 (最高 15)
    if p.has_por:
        score += 8
    if p.has_insurance:
        score += 7

    # 历史安全事件 (扣分)
    for incident in (p.incident_history or []):
        sev = incident.get("severity", "low") if isinstance(incident, dict) else "low"
        score += {"critical": -20, "high": -12, "medium": -6, "low": -3}.get(sev, -3)

    # TVL/规模 (DeFi, 最高 10)
    if p.venue == "DeFi":
        if p.tvl_usd >= 5e9: score += 10
        elif p.tvl_usd >= 1e9: score += 8
        elif p.tvl_usd >= 1e8: score += 5
        elif p.tvl_usd >= 1e7: score += 2

    # 合约可升级扣分
    if p.contract_upgradeable:
        score -= 5

    return max(0, min(100, score))


def _calc_convenience_score(p: ScoredProduct) -> float:
    score = 0

    # 产品类型 (最高 40)
    if p.product_type == "flexible" and p.lock_days == 0:
        score += 40
    elif p.lock_days <= 3: score += 32
    elif p.lock_days <= 7: score += 25
    elif p.lock_days <= 14: score += 18
    elif p.lock_days <= 30: score += 12
    elif p.lock_days <= 90: score += 6
    else: score += 2

    # 赎回速度 (最高 25)
    h = p.redeem_delay_hours
    if h <= 0.1: score += 25
    elif h <= 1: score += 20
    elif h <= 24: score += 12
    elif h <= 168: score += 5

    # KYC (最高 15)
    score += {0: 15, 1: 10, 2: 3}.get(p.kyc_level, 0)

    # 最低门槛 (最高 10)
    if p.min_amount <= 1: score += 10
    elif p.min_amount <= 100: score += 7
    elif p.min_amount <= 1000: score += 3

    # 手续费 (最高 10)
    # TODO: [TECH] 解析 fees dict 为 pct
    score += 10  # 暂默认无手续费

    return max(0, min(100, score))


def _calc_stability_score(p: ScoredProduct) -> float:
    if p.apy_30d_avg <= 0:
        return 50
    cv = p.apy_30d_std / p.apy_30d_avg
    return max(0, min(100, round(100 * (1 - cv))))


def _calc_capacity_score(p: ScoredProduct, user_amount: float) -> float:
    cap = p.remaining_capacity
    if cap is None:
        return 100
    if cap <= 0:
        return 0
    ratio = cap / max(user_amount, 1)
    if ratio >= 10: return 100
    elif ratio >= 2: return 85
    elif ratio >= 1: return 65
    else: return 30


def _find_tier_rate(tiers: dict, amount: float) -> float:
    """
    解析 Binance 阶梯利率 {"0-5BTC": 0.05, "5-10BTC": 0.03} → 适用利率。

    TODO: [TECH] 完善各种格式解析:
      - Binance: "0-5BTC"
      - OKX: 可能是 [{min, max, rate}]
      - 需处理 USDT 金额 vs BTC 数量的单位转换
    """
    if not tiers:
        return 0
    # 简化: 取第一个 tier 的 rate (小额用户通常命中最高档)
    first_rate = list(tiers.values())[0]
    return float(first_rate) * 100 if float(first_rate) < 1 else float(first_rate)


def _norm(value: float, lo: float, hi: float) -> float:
    return max(0, min(1, (value - lo) / max(hi - lo, 0.01)))


# ═══════════════════════════════════════════════════
# L2 总入口
# ═══════════════════════════════════════════════════
def run_l2(
    raw_products: list[RawProduct],
    ctx: UserContext,
    history_map: dict[str, list[float]] = None,
) -> tuple[list[ScoredProduct], MarketStats]:
    """
    L2 总入口。

    参数:
      raw_products: L1 输出
      ctx: 用户参数
      history_map: {source_id: [apy, apy, ...]} — 可选, 用于稳定性计算

    返回:
      (ranked_products, market_stats)
    """
    history_map = history_map or {}

    # Step 1: Filter
    filtered = filter_products(raw_products, ctx)
    logger.info(f"L2 filter: {len(raw_products)} → {len(filtered)}")

    # Step 2+3: Enrich + Derive
    scored = []
    for p in filtered:
        sp = enrich(p)
        history = history_map.get(p.source_id, [])
        sp = derive(sp, history, ctx)
        scored.append(sp)

    # Step 4+5: Score
    for sp in scored:
        score(sp, ctx)

    # Step 6: Rank
    scored = rank(scored)

    # Step 7: Anomaly
    scored = detect_anomalies(scored)

    # Market stats
    stats = calc_market_stats(scored)

    logger.info(f"L2 done: {len(scored)} scored, top={scored[0].composite_score if scored else 'N/A'}")
    return scored, stats
