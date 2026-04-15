"""
L1 数据源: Binance Simple Earn API
Fallback 通道 — 当 Antseer CEX 数据不可用时直连。
"""
import hmac
import hashlib
import time
import httpx
from implementation.pipeline.l1_data.schema import RawProduct

BINANCE_BASE = "https://api.binance.com"
TIMEOUT_S = 10

# TODO: [TECH] 从环境变量或 Vault 读取
BINANCE_API_KEY = ""
BINANCE_SECRET = ""


def _sign(params: dict) -> dict:
    """Binance HMAC-SHA256 签名。"""
    params["timestamp"] = int(time.time() * 1000)
    qs = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    sig = hmac.new(BINANCE_SECRET.encode(), qs.encode(), hashlib.sha256).hexdigest()
    params["signature"] = sig
    return params


async def fetch_flexible_products(asset: str = "") -> list[dict]:
    """
    GET /sapi/v1/simple-earn/flexible/list
    需要 API Key (USER_DATA 级别)。
    """
    url = f"{BINANCE_BASE}/sapi/v1/simple-earn/flexible/list"
    params = {"size": 100}
    if asset:
        params["asset"] = asset
    params = _sign(params)
    headers = {"X-MBX-APIKEY": BINANCE_API_KEY}

    async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
        resp = await client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    return data.get("rows", [])


async def fetch_locked_products(asset: str = "") -> list[dict]:
    """
    GET /sapi/v1/simple-earn/locked/list
    """
    url = f"{BINANCE_BASE}/sapi/v1/simple-earn/locked/list"
    params = {"size": 100}
    if asset:
        params["asset"] = asset
    params = _sign(params)
    headers = {"X-MBX-APIKEY": BINANCE_API_KEY}

    async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
        resp = await client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    return data.get("rows", [])


def normalize_binance_flexible(raw: dict) -> RawProduct:
    """Binance Flexible → RawProduct。字段映射见 PRD §1.3.2。"""
    return RawProduct(
        source_id=raw.get("productId", ""),
        venue="CEX",
        platform_slug="binance",
        platform_name="Binance",
        product_name=f"Flexible {raw.get('asset', '')}",
        asset_symbol=raw.get("asset", ""),
        apy_total=float(raw.get("latestAnnualPercentageRate", 0)) * 100,
        apr_tiers=raw.get("tierAnnualPercentageRate"),
        product_type="flexible",
        lock_days=0,
        min_amount=float(raw.get("minPurchaseAmount", 0)),
        is_sold_out=raw.get("isSoldOut", False),
        available=raw.get("canPurchase", True),
        source_api="binance",
        raw_json=raw,
    )


def normalize_binance_locked(raw: dict) -> RawProduct:
    """Binance Locked → RawProduct。"""
    detail = raw.get("detail", {})
    quota = raw.get("quota", {})
    return RawProduct(
        source_id=raw.get("projectId", ""),
        venue="CEX",
        platform_slug="binance",
        platform_name="Binance",
        product_name=f"Locked {detail.get('asset', '')} {detail.get('duration', '')}d",
        asset_symbol=detail.get("asset", ""),
        apy_total=float(detail.get("apr", 0)) * 100,
        product_type="locked",
        lock_days=int(detail.get("duration", 0)),
        min_amount=float(quota.get("minimum", 0)),
        max_per_user=float(quota.get("totalPersonalQuota", 0)) or None,
        is_sold_out=detail.get("isSoldOut", False),
        available=detail.get("status") == "CREATED",
        source_api="binance",
        raw_json=raw,
    )
