"""DefiLlama 期权类 DeFi 协议 (Ribbon, Thetanuts, Cega 等)"""
from typing import List
from ..schema import RawProduct, VenueType, Side

# DefiLlama yields API: GET https://yields.llama.fi/pools
# Filter: category == "Options" or project in KNOWN_OPTION_PROTOCOLS

KNOWN_OPTION_PROTOCOLS = ["ribbon", "thetanuts", "cega", "friktion", "katana"]

async def fetch_defi_options(underlyings: List[str]) -> List[RawProduct]:
    """
    Fetch from DefiLlama yields, filter option vaults, normalize to RawProduct.
    注意: DefiLlama 的 option vault 数据不含精确 strike/duration，
    需要从 vault name 解析或标记为 estimated。
    """
    # TODO [P2]: 实现 HTTP GET + normalize
    # vault name 格式通常是 "T-BTC-C" (covered call) → side=SELL_HIGH
    # APY 字段为 apy, TVL 字段为 tvlUsd
    return []
