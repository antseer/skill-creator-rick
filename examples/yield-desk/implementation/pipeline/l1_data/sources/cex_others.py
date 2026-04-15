"""
L1 数据源: 其他 CEX Earn API 存根
每家 CEX 需要独立实现 fetch + normalize 函数。

TODO: [TECH] 以下每家交易所需要完成:
  1. 确认 API endpoint + 认证方式
  2. 实现 fetch_products() async 函数
  3. 实现 normalize_xxx() → RawProduct 映射
  4. 处理各家特有的字段差异 (阶梯利率/限额/赎回规则)
"""
import httpx
from implementation.pipeline.l1_data.schema import RawProduct

TIMEOUT_S = 10


# ═══════════════════════════════════════════════════
# OKX Finance
# 文档: https://www.okx.com/docs-v5/en/#rest-api-funding-get-saving-balance
# ═══════════════════════════════════════════════════

# TODO: [TECH] OKX API Key + Secret + Passphrase (环境变量)
OKX_API_KEY = ""
OKX_SECRET = ""
OKX_PASSPHRASE = ""

async def fetch_okx_savings() -> list[dict]:
    """
    GET /api/v5/finance/savings/lending-rate-summary
    返回各币种的活期借贷利率。
    """
    # TODO: [TECH] 实现 OKX 签名 + 请求
    return []

async def fetch_okx_staking() -> list[dict]:
    """
    GET /api/v5/finance/staking-defi/offers
    返回锁仓/Staking 产品。
    """
    # TODO: [TECH] 实现
    return []

def normalize_okx(raw: dict) -> RawProduct:
    """
    OKX 字段映射 (PRD §1.3.3):
      ccy → asset_symbol
      rate → apy_total (×100)
      productType → product_type
      term → lock_days
      minAmt → min_amount
    """
    # TODO: [TECH] 实现
    return RawProduct(source_id="", venue="CEX", platform_slug="okx",
                      platform_name="OKX", product_name="", asset_symbol="")


# ═══════════════════════════════════════════════════
# Bybit Earn
# 文档: https://bybit-exchange.github.io/docs/v5/earn
# ═══════════════════════════════════════════════════

async def fetch_bybit_products() -> list[dict]:
    """
    GET /v5/earn/product/list
    TODO: [TECH] 确认 Bybit Earn API 是否需要 Key
    """
    # TODO: [TECH] 实现
    return []

def normalize_bybit(raw: dict) -> RawProduct:
    # TODO: [TECH] 实现
    return RawProduct(source_id="", venue="CEX", platform_slug="bybit",
                      platform_name="Bybit", product_name="", asset_symbol="")


# ═══════════════════════════════════════════════════
# Bitget Earn
# 文档: https://www.bitget.com/api-doc/earn
# ═══════════════════════════════════════════════════

async def fetch_bitget_products() -> list[dict]:
    """
    GET /api/v2/earn/savings/product
    TODO: [TECH] 实现
    """
    return []

def normalize_bitget(raw: dict) -> RawProduct:
    # TODO: [TECH] 实现
    return RawProduct(source_id="", venue="CEX", platform_slug="bitget",
                      platform_name="Bitget", product_name="", asset_symbol="")


# ═══════════════════════════════════════════════════
# KuCoin Earn
# ═══════════════════════════════════════════════════

async def fetch_kucoin_products() -> list[dict]:
    """
    GET /api/v3/earn/saving/products
    TODO: [TECH] 实现
    """
    return []

def normalize_kucoin(raw: dict) -> RawProduct:
    # TODO: [TECH] 实现
    return RawProduct(source_id="", venue="CEX", platform_slug="kucoin",
                      platform_name="KuCoin", product_name="", asset_symbol="")


# ═══════════════════════════════════════════════════
# Gate.io Earn
# ═══════════════════════════════════════════════════

async def fetch_gate_products() -> list[dict]:
    """
    GET /api/v4/earn/uni/lends
    TODO: [TECH] 实现
    """
    return []

def normalize_gate(raw: dict) -> RawProduct:
    # TODO: [TECH] 实现
    return RawProduct(source_id="", venue="CEX", platform_slug="gate",
                      platform_name="Gate.io", product_name="", asset_symbol="")


# ═══════════════════════════════════════════════════
# HTX (Huobi) Earn
# ═══════════════════════════════════════════════════

async def fetch_htx_products() -> list[dict]:
    """
    GET /v2/earn/products
    TODO: [TECH] 实现
    """
    return []

def normalize_htx(raw: dict) -> RawProduct:
    # TODO: [TECH] 实现
    return RawProduct(source_id="", venue="CEX", platform_slug="htx",
                      platform_name="HTX", product_name="", asset_symbol="")
