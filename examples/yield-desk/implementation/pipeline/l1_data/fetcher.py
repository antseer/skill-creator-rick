"""
L1 统一数据获取器
优先走 Antseer, 失败时 fallback 到各 API 直连。
"""
import asyncio
from dataclasses import fields
import logging
from typing import Optional
from implementation.pipeline.l1_data.schema import RawProduct
from implementation.pipeline.l1_data.sources import antseer, defillama, binance, cex_others

logger = logging.getLogger("yield-desk.l1")


async def fetch_all_products(
    assets: list[str],
    venues: list[str],
) -> list[RawProduct]:
    """
    主入口: 获取全部产品, 返回 RawProduct[]。

    策略:
      1. 先尝试 Antseer MCP (一次拿全)
      2. 如果 Antseer 失败/不完整 → fallback 到各 API 并发
      3. 合并去重
    """
    products: list[RawProduct] = []

    # ── Phase 1: 尝试 Antseer ──
    try:
        raw_list = await antseer.fetch_yield_products(assets, venues)
        if raw_list and len(raw_list) > 10:
            # Antseer 返回数据充分, 直接用
            # TODO: [TECH] Antseer 返回的数据已经是 RawProduct 格式
            #       还是需要 normalize? 取决于 Antseer 接口设计
            for raw in raw_list:
                products.append(_dict_to_raw_product(raw))
            logger.info(f"Antseer: {len(products)} products fetched")
            return products
    except Exception as e:
        logger.warning(f"Antseer failed, falling back: {e}")

    # ── Phase 2: Fallback 并发直连 ──
    tasks = []

    if "DeFi" in venues:
        tasks.append(_fetch_defillama(assets))

    if "CEX" in venues:
        tasks.append(_fetch_binance(assets))
        tasks.append(_fetch_okx(assets))
        tasks.append(_fetch_bybit(assets))
        tasks.append(_fetch_bitget(assets))
        tasks.append(_fetch_kucoin(assets))
        tasks.append(_fetch_gate(assets))
        tasks.append(_fetch_htx(assets))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, Exception):
            logger.warning(f"Source failed: {result}")
            continue
        if isinstance(result, list):
            products.extend(result)

    # ── 去重 (source_id + platform_slug) ──
    seen = set()
    deduped = []
    for p in products:
        key = f"{p.platform_slug}:{p.source_id}"
        if key not in seen:
            seen.add(key)
            deduped.append(p)

    logger.info(f"Fallback total: {len(deduped)} products from {len(tasks)} sources")
    return deduped


async def fetch_pool_history(
    source_api: str,
    pool_id: str,
    days: int = 30,
) -> list[float]:
    """
    获取单池历史 APY 序列。
    优先 Antseer, 降级到 DefiLlama。
    CEX 产品无历史, 返回空。
    """
    if source_api != "defillama":
        return []

    try:
        records = await defillama.fetch_pool_history(pool_id)
        return [r.get("apy", 0) for r in records[-days:]]
    except Exception as e:
        logger.warning(f"Pool history fetch failed for {pool_id}: {e}")
        return []


# ═══════════════════════════════════════════════════
# Fallback 各源适配
# ═══════════════════════════════════════════════════

async def _fetch_defillama(assets: list[str]) -> list[RawProduct]:
    """DefiLlama 拉取 + 过滤稳定币 + normalize。"""
    try:
        pools = await defillama.fetch_defi_pools()
    except Exception as e:
        logger.warning(f"DefiLlama failed: {e}")
        return []

    asset_set = {a.upper() for a in assets}
    result = []
    for raw in pools:
        # 基础过滤: 仅稳定币、TVL > 100K
        if not raw.get("stablecoin"):
            continue
        symbol = raw.get("symbol", "").split("-")[0].upper()
        if symbol not in asset_set:
            continue
        if (raw.get("tvlUsd") or 0) < 100_000:
            continue
        result.append(defillama.normalize_defillama_pool(raw))
    return result


async def _fetch_binance(assets: list[str]) -> list[RawProduct]:
    """Binance Flexible + Locked。"""
    result = []
    try:
        for asset in assets:
            flex = await binance.fetch_flexible_products(asset)
            for raw in flex:
                result.append(binance.normalize_binance_flexible(raw))
            locked = await binance.fetch_locked_products(asset)
            for raw in locked:
                result.append(binance.normalize_binance_locked(raw))
    except Exception as e:
        logger.warning(f"Binance failed: {e}")
    return result


async def _fetch_okx(assets: list[str]) -> list[RawProduct]:
    # TODO: [TECH] 调用 cex_others.fetch_okx_* + normalize
    return []


async def _fetch_bybit(assets: list[str]) -> list[RawProduct]:
    # TODO: [TECH] 调用 cex_others.fetch_bybit_* + normalize
    return []


async def _fetch_bitget(assets: list[str]) -> list[RawProduct]:
    # TODO: [TECH] 同上
    return []


async def _fetch_kucoin(assets: list[str]) -> list[RawProduct]:
    # TODO: [TECH] 同上
    return []


async def _fetch_gate(assets: list[str]) -> list[RawProduct]:
    # TODO: [TECH] 同上
    return []


async def _fetch_htx(assets: list[str]) -> list[RawProduct]:
    # TODO: [TECH] 同上
    return []


def _dict_to_raw_product(d: dict) -> RawProduct:
    """通用 dict → RawProduct, 用于 Antseer 返回。"""
    # TODO: [TECH] 根据 Antseer 实际返回结构调整
    valid = {f.name for f in fields(RawProduct)}
    return RawProduct(**{k: v for k, v in d.items() if k in valid})
