"""
L1 数据源: DefiLlama Yields API
Fallback 通道 — 当 Antseer DeFi 数据不可用时直连。
"""
import httpx
from implementation.pipeline.l1_data.schema import RawProduct

# DefiLlama 免费端点 (Pro 端点需 key)
DEFILLAMA_YIELDS_URL = "https://yields.llama.fi/pools"
DEFILLAMA_HISTORY_URL = "https://yields.llama.fi/chart"  # + /{pool_uuid}
TIMEOUT_S = 15

# TODO: [TECH] 如果使用 Pro 端点 (推荐, 更稳定):
# DEFILLAMA_PRO_BASE = "https://pro-api.llama.fi/{API_KEY}"
# DEFILLAMA_YIELDS_URL = f"{DEFILLAMA_PRO_BASE}/yields/pools"


async def fetch_defi_pools() -> list[dict]:
    """
    拉取 DefiLlama 全量收益池。
    免费端点无需认证, 但限流 ~500 req/5min。
    返回约 12000+ 池, 需在上层过滤。
    """
    async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
        resp = await client.get(DEFILLAMA_YIELDS_URL)
        resp.raise_for_status()
        data = resp.json()

    # DefiLlama 格式: {"status": "success", "data": [...]}
    pools = data.get("data", []) if isinstance(data, dict) else data
    return pools


async def fetch_pool_history(pool_uuid: str) -> list[dict]:
    """
    拉取单池历史 APY/TVL (日粒度, 最多 365 天)。

    返回: [{"timestamp": "2024-01-15T00:00:00.000Z", "apy": 5.2, "tvlUsd": 1e9}, ...]
    """
    url = f"{DEFILLAMA_HISTORY_URL}/{pool_uuid}"
    async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

    return data.get("data", []) if isinstance(data, dict) else data


def normalize_defillama_pool(raw: dict) -> RawProduct:
    """
    DefiLlama 原始池数据 → RawProduct 标准化。
    字段映射见 PRD §1.3.1。
    """
    return RawProduct(
        source_id=raw.get("pool", ""),
        venue="DeFi",
        platform_slug=raw.get("project", ""),
        platform_name=raw.get("project", "").replace("-", " ").title(),
        product_name=f"{raw.get('symbol', '')} {raw.get('poolMeta', 'Pool')}",
        asset_symbol=_extract_primary_asset(raw.get("symbol", "")),
        chain=raw.get("chain"),
        apy_total=raw.get("apy", 0) or 0,
        apy_base=raw.get("apyBase"),
        apy_reward=raw.get("apyReward"),
        reward_tokens=raw.get("rewardTokens", []) or [],
        apy_base_7d=raw.get("apyBase7d"),
        product_type="flexible",  # DeFi 大部分活期, Pendle PT 等在 enrich 里覆盖
        lock_days=0,
        min_amount=0,
        tvl_usd=raw.get("tvlUsd", 0) or 0,
        pool_meta=raw.get("poolMeta"),
        exposure=raw.get("exposure"),
        is_stablecoin=raw.get("stablecoin", False),
        source_api="defillama",
        raw_json=raw,
    )


def _extract_primary_asset(symbol: str) -> str:
    """从 'USDC-ETH' 或 'USDC' 提取主资产。"""
    parts = symbol.split("-")
    return parts[0].strip().upper() if parts else symbol.upper()
