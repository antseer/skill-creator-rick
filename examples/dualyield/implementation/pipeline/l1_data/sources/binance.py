"""Binance DCI + Market Data — 完整实现（需填 API Key）"""
import time, hashlib, hmac, logging
from typing import List
from ..schema import RawProduct, MarketData, Candle, Side, VenueType

logger = logging.getLogger("dualyield.l1.binance")

# TODO [P0]: 填入 Binance API Key/Secret
BINANCE_API_KEY = ""
BINANCE_SECRET = ""
BASE = "https://api.binance.com"

def _sign(params: dict) -> dict:
    params["timestamp"] = int(time.time() * 1000)
    query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    sig = hmac.new(BINANCE_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    params["signature"] = sig
    return params

async def fetch_binance_dci(underlyings: List[str]) -> List[RawProduct]:
    """
    GET /sapi/v1/dci/product/list
    Requires: signed endpoint, read permission
    Response: [{exercisePrice, apr, investCurrency, duration, ...}]
    """
    # TODO [P1]: 实现 HTTP 调用，以下为字段映射参考
    # product_id = f"binance_{item['id']}"
    # side = Side.BUY_LOW if item['optionType'] == 'PUT' else Side.SELL_HIGH
    # strike = float(item['exercisePrice'])
    # apr = float(item['apr'])
    # duration_days = int(item['duration'])
    # min_amount = float(item['minAmount'])
    raise NotImplementedError("Fill BINANCE_API_KEY first")

async def fetch_binance_market(underlying: str) -> MarketData:
    """
    GET /api/v3/klines?symbol={underlying}USDT&interval=1h&limit=1000
    GET /api/v3/klines?symbol={underlying}USDT&interval=1d&limit=180
    GET /api/v3/ticker/price?symbol={underlying}USDT
    这些是公开端点，不需要签名。
    """
    raise NotImplementedError("Implement Binance public klines fetch")
