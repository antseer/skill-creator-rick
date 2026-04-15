"""L2 Compute Schema — 计算层数据结构"""
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

class Intent(Enum):
    EARN_YIELD = "earn_yield"   # 只想吃利率
    BUY_DIP = "buy_dip"        # 想低价接货
    SELL_HIGH = "sell_high"     # 想高价出货

class RiskLevel(Enum):
    CONSERVATIVE = "conservative"  # P(touch) ≤ 5%
    BALANCED = "balanced"          # P(touch) ≤ 15%
    AGGRESSIVE = "aggressive"      # P(touch) ≤ 30%

RISK_PTOUCH_CAP = {
    RiskLevel.CONSERVATIVE: 0.05,
    RiskLevel.BALANCED: 0.15,
    RiskLevel.AGGRESSIVE: 0.30,
}

@dataclass
class UserContext:
    intent: Intent = Intent.EARN_YIELD
    underlying: str = "BTC"
    principal: float = 10000.0
    durations: List[int] = field(default_factory=lambda: [7, 14])
    risk: RiskLevel = RiskLevel.BALANCED
    target_price: Optional[float] = None  # 仅 buy_dip/sell_high 时使用

@dataclass
class SRLevel:
    price: float
    strength: int   # 触碰次数
    kind: str       # "support" / "resistance"

@dataclass
class TAResult:
    """技术分析结果"""
    current_price: float
    ma20: float
    ma60: float
    ma120: float
    rsi14: float
    macd_line: float
    macd_signal: float
    macd_hist: float
    hist_vol_annual: float  # 历史波动率（年化）
    trend: str              # "bullish" / "bearish" / "neutral"
    sr_levels: List[SRLevel] = field(default_factory=list)

@dataclass
class ScoredProduct:
    """L2 计算后的评分产品"""
    product_id: str
    platform: str
    venue_type: str
    underlying: str
    side: str
    strike: float
    duration_days: int
    apr: float
    min_amount: float
    max_amount: Optional[float]
    # --- L2 enriched ---
    distance_pct: float        # |strike - spot| / spot
    touch_prob: float          # 首次通过概率
    near_sr: bool              # 是否靠近支撑/阻力位
    sr_type: Optional[str]     # "support" / "resistance" / None
    # --- L2 scored ---
    score: float               # 综合得分
    rank: int = 0
    anomaly_flags: List[str] = field(default_factory=list)

@dataclass
class PlatformTier:
    platform: str
    tier: int       # 1=顶级, 2=主流, 3=新兴
    has_por: bool
    audit_count: int
