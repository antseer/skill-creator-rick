"""OKX / Bybit / Bitget / Deribit DCI 数据源存根"""
from typing import List
from ..schema import RawProduct

# ========== OKX ==========
# POST https://www.okx.com/api/v5/finance/staking-defi/eth/purchase
# 文档: https://www.okx.com/docs-v5/en/#financial-product
async def fetch_okx_dci(underlyings: List[str]) -> List[RawProduct]:
    # TODO [P1]: OKX 双币赢 API 实现
    return []

# ========== Bybit ==========
# GET https://api.bybit.com/v5/earn/dual-investment/product/list
async def fetch_bybit_dci(underlyings: List[str]) -> List[RawProduct]:
    # TODO [P1]: Bybit 双币投 API 实现
    return []

# ========== Bitget ==========
# GET https://api.bitget.com/api/v2/earn/sharkfin/product-list
async def fetch_bitget_dci(underlyings: List[str]) -> List[RawProduct]:
    # TODO [P1]: Bitget 鲨鱼鳍/双币投 API 实现
    return []

# ========== Deribit IV ==========
# GET https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency=BTC&kind=option
async def fetch_deribit_iv(underlying: str):
    """获取 Deribit 期权链 IV，用于补充波动率估算"""
    # TODO [P2]: 实现 Deribit 公开 API 调用
    return []
