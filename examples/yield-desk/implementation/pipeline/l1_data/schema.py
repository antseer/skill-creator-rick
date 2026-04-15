"""
L1 数据层 Schema — RawProduct
所有数据源统一标准化到此结构后交给 L2。
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class RawProduct:
    """L1 输出：一个可投资产品的原始标准化数据。"""

    # ── 身份 ──
    source_id: str                          # 来源方内部 ID (UUID / productId)
    venue: str                              # "CEX" | "DeFi"
    platform_slug: str                      # "binance" / "aave-v3"
    platform_name: str                      # 展示名
    product_name: str                       # "Flexible USDC" / "USDC Supply"
    asset_symbol: str                       # "USDT" / "USDC" / "DAI"
    chain: Optional[str] = None             # DeFi 有, CEX 为 null

    # ── 收益 (L1 原始) ──
    apy_total: float = 0.0                  # 总 APY %
    apy_base: Optional[float] = None        # 基础 APY
    apy_reward: Optional[float] = None      # 奖励部分
    reward_tokens: list[str] = field(default_factory=list)
    apy_base_7d: Optional[float] = None
    apr_tiers: Optional[dict] = None        # Binance 阶梯利率 {"0-5BTC": 0.05, ...}

    # ── 产品属性 ──
    product_type: str = "flexible"          # "flexible" | "locked" | "structured"
    lock_days: int = 0                      # 0 = 活期
    min_amount: float = 0.0
    max_per_user: Optional[float] = None
    is_sold_out: bool = False
    available: bool = True

    # ── 规模 ──
    tvl_usd: float = 0.0
    remaining_capacity: Optional[float] = None

    # ── 安全 (L1 能拿到的) ──
    pool_meta: Optional[str] = None         # "Lending" / "LP" / "RWA"
    exposure: Optional[str] = None          # "single" / "multi"
    is_stablecoin: bool = True

    # ── 元数据 ──
    source_api: str = ""                    # "defillama" / "binance" / ...
    fetched_at: str = ""                    # ISO timestamp
    raw_json: dict = field(default_factory=dict)  # 信任层展示

    def __post_init__(self):
        if not self.fetched_at:
            self.fetched_at = datetime.utcnow().isoformat() + "Z"
