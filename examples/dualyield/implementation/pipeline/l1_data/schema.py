"""L1 Data Schema — RawProduct, Candle, MarketData"""
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum

class Side(Enum):
    BUY_LOW = "buy_low"
    SELL_HIGH = "sell_high"

class VenueType(Enum):
    CEX = "cex"
    DEFI = "defi"

@dataclass
class RawProduct:
    product_id: str
    platform: str
    venue_type: VenueType
    currency: str
    underlying: str
    side: Side
    strike: float
    duration_days: int
    apr: float
    min_amount: float
    max_amount: Optional[float] = None
    settlement_ccy: str = "USDT"
    fetched_at: float = 0.0

@dataclass
class Candle:
    ts: float
    o: float
    h: float
    l: float
    c: float
    v: float

@dataclass
class OptionIV:
    strike: float
    expiry_days: int
    iv: float
    source: str

@dataclass
class MarketData:
    underlying: str
    spot_price: float
    candles_1h: List[Candle] = field(default_factory=list)
    candles_1d: List[Candle] = field(default_factory=list)
    iv_chain: List[OptionIV] = field(default_factory=list)
    fetched_at: float = 0.0
