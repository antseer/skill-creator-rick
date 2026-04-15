"""
L2 计算层 Schema — ScoredProduct
在 RawProduct 基础上补全安全元数据 + 计算派生字段 + 多维评分。
"""
from dataclasses import dataclass, field
from typing import Optional
from implementation.pipeline.l1_data.schema import RawProduct


@dataclass
class Audit:
    firm: str
    date: Optional[str] = None
    url: Optional[str] = None


@dataclass
class FeeInfo:
    subscribe: str = "0"
    redeem: str = "0"
    mgmt: str = "0"
    gas_est: str = "N/A"


@dataclass
class ScoredProduct(RawProduct):
    """L2 输出：含评分的完整产品数据。"""

    # ── 补全字段 (from platform_meta / protocol_meta) ──
    tier: int = 3
    audits: list = field(default_factory=list)
    has_insurance: bool = False
    has_por: bool = False
    last_por_at: Optional[str] = None
    incident_history: list = field(default_factory=list)
    kyc_level: int = 0                      # 0=免KYC, 1=基础, 2=高级
    restricted_regions: list[str] = field(default_factory=list)
    contract_upgradeable: Optional[bool] = None
    multisig_signers: Optional[int] = None
    site_url: str = ""
    yield_source: str = ""                  # "lending"/"lp"/"rwa"/"structured"/"delta-neutral"
    redeem_delay_hours: float = 0.0
    fees: dict = field(default_factory=dict)

    # ── 派生字段 ──
    apy_30d_avg: float = 0.0
    apy_30d_std: float = 0.0
    apy_7d_trend: float = 0.0
    apy_without_reward: float = 0.0
    reward_dependency: float = 0.0
    effective_apy: float = 0.0              # 考虑阶梯后的实际利率

    # ── 评分字段 ──
    security_score: float = 0.0             # 0-100
    convenience_score: float = 0.0          # 0-100
    stability_score: float = 0.0            # 0-100
    capacity_score: float = 0.0             # 0-100
    composite_score: float = 0.0            # 0-100 加权综合

    # ── 排名 ──
    rank: int = 0

    # ── 异常标记 ──
    anomaly_flags: list[str] = field(default_factory=list)

    # ── 雷达图归一化值 ──
    radar: dict = field(default_factory=lambda: {
        "apy": 0.0, "sec": 0.0, "conv": 0.0, "cap": 0.0, "stab": 0.0,
    })


@dataclass
class UserContext:
    """用户侧参数，来自前端 Sidebar。"""
    assets: list[str] = field(default_factory=lambda: ["USDT", "USDC"])
    venues: list[str] = field(default_factory=lambda: ["CEX", "DeFi"])
    amount: float = 10000.0
    sec_priority: str = "balanced"          # "tier1" / "balanced" / "loose"
    conv_priority: str = "balanced"         # "flex" / "balanced" / "any"
    kyc: str = "basic"                      # "none" / "basic" / "any"


@dataclass
class MarketStats:
    """市场均值统计，喂给 L3。"""
    avg_apy: float = 0.0
    median_apy: float = 0.0
    count: int = 0
