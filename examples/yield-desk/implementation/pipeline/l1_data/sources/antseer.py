"""
L1 数据源: Antseer MCP / REST API
主通道 — 一次调用获取全部 CEX + DeFi 聚合数据。
"""
import httpx
from typing import Optional
from implementation.pipeline.l1_data.schema import RawProduct

# ═══════════════════════════════════════════════════
# TODO: [TECH] 以下常量需根据 Antseer 实际文档填写
# ═══════════════════════════════════════════════════
ANTSEER_BASE_URL = "https://api.antseer.ai/v1"  # TODO: [TECH] 确认真实 base URL
ANTSEER_API_KEY = ""                              # TODO: [TECH] 从环境变量读取
TIMEOUT_S = 10


async def fetch_yield_products(
    assets: list[str],
    venues: list[str],
) -> list[dict]:
    """
    调用 Antseer 聚合端点，获取全部 Earn 产品。

    TODO: [TECH] 需要 Antseer 实现以下端点:
      GET /api/v1/earn/products?asset=USDT,USDC&venue=CEX,DeFi

    期望返回:
      [{
        source_id, venue, platform_slug, platform_name, product_name,
        asset_symbol, chain, apy_total, apy_base, apy_reward,
        reward_tokens, product_type, lock_days, min_amount,
        max_per_user, is_sold_out, available, tvl_usd,
        remaining_capacity, pool_meta, exposure, is_stablecoin,
        apr_tiers, apy_base_7d
      }]
    """
    url = f"{ANTSEER_BASE_URL}/earn/products"
    params = {
        "asset": ",".join(assets),
        "venue": ",".join(venues),
    }
    headers = {
        "Authorization": f"Bearer {ANTSEER_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
        resp = await client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    # TODO: [TECH] 根据 Antseer 实际响应结构解析
    # 预期 data 直接是 list[dict] 或 data["products"]
    return data.get("products", data) if isinstance(data, dict) else data


async def fetch_pool_history(pool_id: str, days: int = 30) -> list[float]:
    """
    获取单个池的历史 APY 时序 (日粒度)。

    TODO: [TECH] 需要 Antseer 实现:
      GET /api/v1/yield/history?pool_id=xxx&days=30

    期望返回:
      [5.2, 5.3, 5.1, ...] — 每天一个 APY 值，最新在末尾
    """
    url = f"{ANTSEER_BASE_URL}/yield/history"
    params = {"pool_id": pool_id, "days": days}
    headers = {"Authorization": f"Bearer {ANTSEER_API_KEY}"}

    async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
        resp = await client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    # TODO: [TECH] 根据实际结构提取 APY 序列
    return data.get("apy_series", [])


async def fetch_safety_meta() -> dict:
    """
    获取 CEX + DeFi 安全元数据。

    TODO: [TECH] 需要 Antseer 实现:
      GET /api/v1/safety/meta

    期望返回:
      {
        "binance": {tier: 1, has_por: true, audits: [...], ...},
        "aave-v3": {tier: 1, audits: [...], ...},
        ...
      }
    """
    url = f"{ANTSEER_BASE_URL}/safety/meta"
    headers = {"Authorization": f"Bearer {ANTSEER_API_KEY}"}

    async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()
