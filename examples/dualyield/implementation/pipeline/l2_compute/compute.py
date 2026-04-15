"""
L2 Compute Engine — DualYield Strategist
核心算法: TA指标 → 到达概率 → 评分 → 排序 → 异常检测

关键公式:
  P(touch) = 2 * Φ(-|ln(K/S)| / (σ√T))     # 无漂移GBM首次通过概率
  score = APR×w1 + safety×w2 + ta_bonus×w3   # 意图感知评分
"""
import math
from typing import List, Optional, Tuple
from .schema import (
    UserContext, TAResult, ScoredProduct, SRLevel, PlatformTier,
    Intent, RiskLevel, RISK_PTOUCH_CAP
)

# ============================================================
# 1. 技术分析
# ============================================================

def calc_ma(closes: List[float], period: int) -> float:
    """简单移动平均，数据不足时返回最后一个值"""
    if not closes:
        return 0.0
    if len(closes) < period:
        return sum(closes) / len(closes)
    return sum(closes[-period:]) / period


def calc_rsi(closes: List[float], period: int = 14) -> float:
    """
    RSI(14) — 相对强弱指标
    修复: 全部持平时返回 50.0 (中性)，而非 100 或 0
    """
    if len(closes) < period + 1:
        return 50.0
    changes = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    recent = changes[-(period):]
    gains = [c for c in recent if c > 0]
    losses = [-c for c in recent if c < 0]
    avg_gain = sum(gains) / period if gains else 0.0
    avg_loss = sum(losses) / period if losses else 0.0
    if avg_gain == 0 and avg_loss == 0:
        return 50.0  # FIX: 持平 → 中性
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def calc_macd(closes: List[float]) -> Tuple[float, float, float]:
    """MACD(12,26,9) → (macd_line, signal, histogram)"""
    def ema(data, period):
        if not data:
            return 0.0
        if len(data) < period:
            return sum(data) / len(data)
        k = 2 / (period + 1)
        val = sum(data[:period]) / period
        for p in data[period:]:
            val = p * k + val * (1 - k)
        return val

    if len(closes) < 26:
        return 0.0, 0.0, 0.0

    ema12 = ema(closes, 12)
    ema26 = ema(closes, 26)
    macd_line = ema12 - ema26

    # 简化: 用最后 9 个差值的 EMA 近似 signal
    if len(closes) >= 35:
        diffs = []
        for i in range(9):
            idx = len(closes) - 9 + i
            sub = closes[:idx+1]
            e12 = ema(sub, 12)
            e26 = ema(sub, 26)
            diffs.append(e12 - e26)
        signal = ema(diffs, 9)
    else:
        signal = macd_line

    return macd_line, signal, macd_line - signal


def calc_hist_vol(candles_close: List[float], periods_per_year: float) -> float:
    """
    历史波动率（年化）
    candles_close: 收盘价序列
    periods_per_year: 年化因子 (1h蜡烛=8760, 日线=365)

    修复: 正确使用对数收益率 + sqrt(periods_per_year) 年化
    """
    if len(candles_close) < 2:
        return 0.6  # 默认 60%

    log_returns = []
    for i in range(1, len(candles_close)):
        if candles_close[i-1] > 0 and candles_close[i] > 0:
            log_returns.append(math.log(candles_close[i] / candles_close[i-1]))

    if len(log_returns) < 2:
        return 0.6

    mean = sum(log_returns) / len(log_returns)
    variance = sum((r - mean) ** 2 for r in log_returns) / (len(log_returns) - 1)
    sigma_per_period = math.sqrt(variance)
    sigma_annual = sigma_per_period * math.sqrt(periods_per_year)
    return sigma_annual


def find_sr_levels(candles_high: List[float], candles_low: List[float],
                   tolerance_pct: float = 0.015, min_touches: int = 2) -> List[SRLevel]:
    """
    支撑/阻力位识别 — 局部极值聚类法
    1. 找所有局部极大值(阻力候选)和极小值(支撑候选)
    2. 在 tolerance_pct 容差内聚类
    3. 触碰次数 >= min_touches 才算有效
    """
    if len(candles_high) < 5:
        return []

    # 找局部极值 (5 根 K 线窗口)
    resistance_candidates = []
    support_candidates = []
    for i in range(2, len(candles_high) - 2):
        if candles_high[i] >= max(candles_high[i-2:i] + candles_high[i+1:i+3]):
            resistance_candidates.append(candles_high[i])
        if candles_low[i] <= min(candles_low[i-2:i] + candles_low[i+1:i+3]):
            support_candidates.append(candles_low[i])

    def cluster(prices: List[float], kind: str) -> List[SRLevel]:
        if not prices:
            return []
        prices.sort()
        levels = []
        cluster_prices = [prices[0]]
        for p in prices[1:]:
            if abs(p - cluster_prices[0]) / cluster_prices[0] <= tolerance_pct:
                cluster_prices.append(p)
            else:
                if len(cluster_prices) >= min_touches:
                    avg = sum(cluster_prices) / len(cluster_prices)
                    levels.append(SRLevel(price=round(avg, 2),
                                          strength=len(cluster_prices), kind=kind))
                cluster_prices = [p]
        if len(cluster_prices) >= min_touches:
            avg = sum(cluster_prices) / len(cluster_prices)
            levels.append(SRLevel(price=round(avg, 2),
                                  strength=len(cluster_prices), kind=kind))
        return levels

    return cluster(resistance_candidates, "resistance") + cluster(support_candidates, "support")


def run_ta(closes_1d: List[float], highs_1d: List[float],
           lows_1d: List[float], closes_1h: List[float]) -> TAResult:
    """运行完整 TA 分析"""
    if not closes_1d:
        return TAResult(current_price=0, ma20=0, ma60=0, ma120=0,
                        rsi14=50, macd_line=0, macd_signal=0, macd_hist=0,
                        hist_vol_annual=0.6, trend="neutral")

    current = closes_1d[-1]
    ma20 = calc_ma(closes_1d, 20)
    ma60 = calc_ma(closes_1d, 60)
    ma120 = calc_ma(closes_1d, 120)
    rsi = calc_rsi(closes_1d, 14)
    ml, ms, mh = calc_macd(closes_1d)

    # 波动率: 优先用 1h（更精确），降级用日线
    if len(closes_1h) >= 100:
        vol = calc_hist_vol(closes_1h, 8760)  # 1h → 年化
    else:
        vol = calc_hist_vol(closes_1d, 365)   # 日线 → 年化

    # 趋势判断
    if current > ma20 > ma60 and rsi > 50:
        trend = "bullish"
    elif current < ma20 < ma60 and rsi < 50:
        trend = "bearish"
    else:
        trend = "neutral"

    sr = find_sr_levels(highs_1d, lows_1d)

    return TAResult(
        current_price=current, ma20=ma20, ma60=ma60, ma120=ma120,
        rsi14=rsi, macd_line=ml, macd_signal=ms, macd_hist=mh,
        hist_vol_annual=vol, trend=trend, sr_levels=sr
    )


# ============================================================
# 2. 到达概率
# ============================================================

def _norm_cdf(x: float) -> float:
    """标准正态 CDF — 使用 math.erf 精确实现"""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def touch_prob(spot: float, strike: float, vol_annual: float,
               duration_days: int) -> float:
    """
    首次通过概率 — 无漂移 GBM

    公式: P(touch) = 2 * Φ(-|ln(K/S)| / (σ√T))

    其中:
      K = strike, S = spot
      σ = 年化波动率
      T = duration_days / 365 (年)

    推导: 对于 dX = σ dW 的对数布朗运动,
    barrier |ln(K/S)| 的首次通过时间服从反高斯分布,
    P(τ ≤ T) = 2Φ(-d) 其中 d = |ln(K/S)|/(σ√T)

    边界:
      spot == strike → P = 1.0
      vol ≤ 0 or T ≤ 0 → P = 0.0
    """
    if spot <= 0 or strike <= 0:
        return 0.0
    if vol_annual <= 0 or duration_days <= 0:
        return 0.0
    if abs(spot - strike) / spot < 1e-6:
        return 1.0

    T = duration_days / 365.0
    log_dist = abs(math.log(strike / spot))
    denom = vol_annual * math.sqrt(T)
    if denom < 1e-10:
        return 0.0

    d = log_dist / denom
    prob = 2.0 * _norm_cdf(-d)
    return max(0.0, min(1.0, prob))


# ============================================================
# 3. 评分与排序
# ============================================================

# 平台 Tier 得分
PLATFORM_TIER_SCORE = {1: 0.10, 2: 0.05, 3: 0.00}

def score_product(
    product_id: str, platform: str, venue_type: str,
    underlying: str, side: str, strike: float,
    duration_days: int, apr: float, min_amount: float,
    max_amount: Optional[float],
    spot: float, vol: float, ta: TAResult,
    ctx: UserContext, tier: int = 2
) -> ScoredProduct:
    """
    综合评分 — 意图感知

    score = APR_norm × 0.60
          + safety_bonus            (Tier加成, 0~0.10)
          + ta_bonus                (靠近S/R, 0~0.15)
          + intent_bonus            (意图匹配, 0~0.15)
    """
    # 基础指标
    dist_pct = abs(strike - spot) / spot if spot > 0 else 0
    p_touch = touch_prob(spot, strike, vol, duration_days)

    # 是否靠近 S/R
    near_sr = False
    sr_type = None
    for sr in ta.sr_levels:
        if abs(strike - sr.price) / sr.price < 0.01:  # 1%容差
            near_sr = True
            sr_type = sr.kind
            break

    # --- APR 归一化 (0~1, 基于 50% 为满分) ---
    apr_norm = min(apr / 0.50, 1.0)

    # --- 安全加分 ---
    safety = PLATFORM_TIER_SCORE.get(tier, 0)

    # --- TA 加分 ---
    ta_bonus = 0.0
    if near_sr:
        if sr_type == "resistance" and side == "sell_high":
            ta_bonus = 0.15  # 执行价在阻力位附近，高卖合理
        elif sr_type == "support" and side == "buy_low":
            ta_bonus = 0.15  # 执行价在支撑位附近，低买合理
        else:
            ta_bonus = 0.05  # 靠近S/R但方向不完全匹配

    # --- 意图加分 ---
    intent_bonus = 0.0
    if ctx.intent == Intent.EARN_YIELD:
        # 吃息: 越远越好 (低 P_touch)，惩罚高概率
        if p_touch < 0.05:
            intent_bonus = 0.15
        elif p_touch < 0.10:
            intent_bonus = 0.08
    elif ctx.intent == Intent.BUY_DIP and side == "buy_low":
        intent_bonus = 0.12
    elif ctx.intent == Intent.SELL_HIGH and side == "sell_high":
        intent_bonus = 0.12

    score = apr_norm * 0.60 + safety + ta_bonus + intent_bonus

    return ScoredProduct(
        product_id=product_id, platform=platform, venue_type=venue_type,
        underlying=underlying, side=side, strike=strike,
        duration_days=duration_days, apr=apr, min_amount=min_amount,
        max_amount=max_amount, distance_pct=dist_pct, touch_prob=p_touch,
        near_sr=near_sr, sr_type=sr_type, score=score
    )


def filter_by_risk(products: List[ScoredProduct],
                   risk: RiskLevel) -> List[ScoredProduct]:
    """按风险偏好过滤: P(touch) 不超过对应上限"""
    cap = RISK_PTOUCH_CAP[risk]
    return [p for p in products if p.touch_prob <= cap]


def filter_by_intent(products: List[ScoredProduct],
                     intent: Intent) -> List[ScoredProduct]:
    """按意图过滤产品方向"""
    if intent == Intent.BUY_DIP:
        return [p for p in products if p.side == "buy_low"]
    elif intent == Intent.SELL_HIGH:
        return [p for p in products if p.side == "sell_high"]
    else:  # EARN_YIELD — 两个方向都看
        return products


def detect_anomalies(products: List[ScoredProduct]) -> List[ScoredProduct]:
    """
    异常检测 — 标记可疑产品
    规则:
      APR_OUTLIER: APR > 同档位均值 + 2σ
      NEAR_EXPIRY: 期限 ≤ 1天
      SMALL_PLATFORM: venue_type=defi 且 Tier-3
    """
    if len(products) < 3:
        return products

    aprs = [p.apr for p in products]
    mean_apr = sum(aprs) / len(aprs)
    std_apr = math.sqrt(sum((a - mean_apr)**2 for a in aprs) / len(aprs)) if len(aprs) > 1 else 0

    for p in products:
        if std_apr > 0 and p.apr > mean_apr + 2 * std_apr:
            p.anomaly_flags.append("APR_OUTLIER")
        if p.duration_days <= 1:
            p.anomaly_flags.append("NEAR_EXPIRY")

    return products


def rank_and_select(scored: List[ScoredProduct], top_n: int = 3) -> List[ScoredProduct]:
    """排序并赋予 rank，返回 TOP N"""
    scored.sort(key=lambda x: x.score, reverse=True)
    for i, p in enumerate(scored):
        p.rank = i + 1
    return scored[:top_n]


# ============================================================
# 4. 完整 Pipeline
# ============================================================

def run_l2(raw_products: list, market_data: dict, ctx: UserContext,
           platform_tiers: dict = None) -> Tuple[List[ScoredProduct], TAResult]:
    """
    L2 完整执行:
    raw_products → filter(intent) → enrich(TA+score) → filter(risk) → anomaly → rank

    Returns: (top3, ta_result)
    """
    if platform_tiers is None:
        platform_tiers = {}

    # TA
    md = market_data.get(ctx.underlying)
    if md:
        closes_1d = [c.c for c in md.candles_1d]
        highs_1d = [c.h for c in md.candles_1d]
        lows_1d = [c.l for c in md.candles_1d]
        closes_1h = [c.c for c in md.candles_1h]
        ta = run_ta(closes_1d, highs_1d, lows_1d, closes_1h)
        spot = md.spot_price
        vol = ta.hist_vol_annual
    else:
        ta = TAResult(current_price=0, ma20=0, ma60=0, ma120=0,
                      rsi14=50, macd_line=0, macd_signal=0, macd_hist=0,
                      hist_vol_annual=0.6, trend="neutral")
        spot = 100000
        vol = 0.6

    # Score all
    scored = []
    for rp in raw_products:
        if rp.underlying != ctx.underlying:
            continue
        if rp.duration_days not in ctx.durations:
            continue
        tier = platform_tiers.get(rp.platform, 2)
        sp = score_product(
            rp.product_id, rp.platform, rp.venue_type.value if hasattr(rp.venue_type, 'value') else rp.venue_type,
            rp.underlying, rp.side.value if hasattr(rp.side, 'value') else rp.side,
            rp.strike, rp.duration_days, rp.apr, rp.min_amount, rp.max_amount,
            spot, vol, ta, ctx, tier
        )
        scored.append(sp)

    # Filter
    scored = filter_by_intent(scored, ctx.intent)
    scored = filter_by_risk(scored, ctx.risk)
    scored = detect_anomalies(scored)
    top3 = rank_and_select(scored, 3)

    return top3, ta
