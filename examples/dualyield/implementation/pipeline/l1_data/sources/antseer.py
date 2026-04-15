"""
Antseer API 数据源 — 存根，需技术同事填充。
预期端点:
  GET /api/v1/dci/products?underlyings=BTC,ETH
  GET /api/v1/market/{underlying}?candles=1h,1d&days=180
  GET /api/v1/iv/chain?underlying=BTC
文档: https://antseer.ai/docs
"""
from typing import List
from ..schema import RawProduct, MarketData

# TODO [P0]: 确认 Antseer 端点 URL、认证方式、响应结构
# TODO [P0]: 实现字段映射到 RawProduct schema

ANTSEER_BASE = "https://api.antseer.ai/v1"

async def fetch_dci_products(underlyings: List[str]) -> List[RawProduct]:
    raise NotImplementedError("Antseer DCI endpoint not yet configured")

async def fetch_market(underlying: str) -> MarketData:
    raise NotImplementedError("Antseer market endpoint not yet configured")
