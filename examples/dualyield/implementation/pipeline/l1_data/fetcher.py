"""L1 Unified Fetcher — Antseer优先，自动降级到各平台直连"""
import asyncio, time, logging
from typing import List, Tuple
from .schema import RawProduct, MarketData

logger = logging.getLogger("dualyield.l1")

async def fetch_all(underlyings: List[str], use_antseer: bool = True) -> Tuple[List[RawProduct], dict]:
    products: List[RawProduct] = []
    market_data: dict = {}
    t0 = time.time()

    if use_antseer:
        try:
            from .sources.antseer import fetch_dci_products, fetch_market
            products = await fetch_dci_products(underlyings)
            for u in underlyings:
                market_data[u] = await fetch_market(u)
            logger.info(f"Antseer: {len(products)} products in {time.time()-t0:.1f}s")
            return products, market_data
        except Exception as e:
            logger.warning(f"Antseer failed ({e}), falling back")

    from .sources.binance import fetch_binance_dci, fetch_binance_market
    from .sources.cex_others import fetch_okx_dci, fetch_bybit_dci, fetch_bitget_dci
    from .sources.defillama import fetch_defi_options

    results = await asyncio.gather(
        fetch_binance_dci(underlyings), fetch_okx_dci(underlyings),
        fetch_bybit_dci(underlyings), fetch_bitget_dci(underlyings),
        fetch_defi_options(underlyings), return_exceptions=True)
    for r in results:
        if isinstance(r, list): products.extend(r)

    for u in underlyings:
        try: market_data[u] = await fetch_binance_market(u)
        except: pass

    logger.info(f"Fallback: {len(products)} products in {time.time()-t0:.1f}s")
    return products, market_data
