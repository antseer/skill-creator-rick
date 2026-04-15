"""
L2 评分逻辑单测
覆盖: security_score / convenience_score / stability_score / 综合分 / 排序 / 异常检测
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipeline.l1_data.schema import RawProduct
from pipeline.l2_compute.compute import (
    filter_products, enrich, derive, score, rank,
    detect_anomalies, run_l2,
    _calc_security_score, _calc_convenience_score, _calc_stability_score,
)
from pipeline.l2_compute.schema import ScoredProduct, UserContext


def make_raw(**kwargs) -> RawProduct:
    """快速构造测试用 RawProduct。"""
    defaults = dict(
        source_id="test-001", venue="CEX", platform_slug="binance",
        platform_name="Binance", product_name="Flex USDT", asset_symbol="USDT",
        apy_total=8.0, product_type="flexible", lock_days=0, available=True,
        tvl_usd=1e9, source_api="binance",
    )
    defaults.update(kwargs)
    return RawProduct(**defaults)


def make_scored(**kwargs) -> ScoredProduct:
    """快速构造测试用 ScoredProduct。"""
    defaults = dict(
        source_id="test-001", venue="CEX", platform_slug="binance",
        platform_name="Binance", product_name="Flex USDT", asset_symbol="USDT",
        apy_total=8.0, product_type="flexible", lock_days=0, tier=1,
        audits=["A", "B"], has_por=True, has_insurance=True,
        incident_history=[], tvl_usd=1e9,
        apy_30d_avg=8.0, apy_30d_std=0.4, effective_apy=8.0,
        redeem_delay_hours=0.1, kyc_level=1, min_amount=1,
    )
    defaults.update(kwargs)
    return ScoredProduct(**defaults)


# ═══════════════════════════════════════════════
# Security Score
# ═══════════════════════════════════════════════

def test_security_score_tier1_cex():
    sp = make_scored(venue="CEX", tier=1, audits=["A", "B"], has_por=True, has_insurance=True)
    s = _calc_security_score(sp)
    # 40 (tier) + 16 (2 audits) + 8 (por) + 7 (insurance) = 71
    assert s == 71, f"Expected 71, got {s}"

def test_security_score_tier1_defi():
    sp = make_scored(venue="DeFi", tier=1, audits=["A", "B", "C"],
                     has_por=False, has_insurance=True, tvl_usd=6e9)
    s = _calc_security_score(sp)
    # 38 (tier) + 24 (3*8=24, cap 25) + 0 (por) + 7 (ins) + 10 (tvl>=5B) = 79
    assert s == 79, f"Expected 79, got {s}"

def test_security_score_with_incident():
    sp = make_scored(venue="CEX", tier=2, audits=["A"],
                     has_por=True, has_insurance=False,
                     incident_history=[{"severity": "high"}])
    s = _calc_security_score(sp)
    # 25 + 8 + 8 + 0 - 12 = 29
    assert s == 29, f"Expected 29, got {s}"

def test_security_score_floor_zero():
    sp = make_scored(venue="CEX", tier=3, audits=[],
                     has_por=False, has_insurance=False,
                     incident_history=[{"severity": "critical"}, {"severity": "critical"}])
    s = _calc_security_score(sp)
    # 12 + 0 + 0 + 0 - 20 - 20 = -28 → floor 0
    assert s == 0, f"Expected 0, got {s}"


# ═══════════════════════════════════════════════
# Convenience Score
# ═══════════════════════════════════════════════

def test_convenience_flexible():
    sp = make_scored(product_type="flexible", lock_days=0,
                     redeem_delay_hours=0.05, kyc_level=0, min_amount=0)
    s = _calc_convenience_score(sp)
    # 40 + 25 + 15 + 10 + 10 = 100
    assert s == 100, f"Expected 100, got {s}"

def test_convenience_locked_30d():
    sp = make_scored(product_type="locked", lock_days=30,
                     redeem_delay_hours=0, kyc_level=2, min_amount=1000)
    s = _calc_convenience_score(sp)
    # 12 + 25 + 3 + 3 + 10 = 53
    assert s == 53, f"Expected 53, got {s}"


# ═══════════════════════════════════════════════
# Stability Score
# ═══════════════════════════════════════════════

def test_stability_zero_variance():
    sp = make_scored(apy_30d_avg=5.0, apy_30d_std=0.0)
    s = _calc_stability_score(sp)
    assert s == 100, f"Expected 100, got {s}"

def test_stability_high_variance():
    sp = make_scored(apy_30d_avg=10.0, apy_30d_std=5.0)
    s = _calc_stability_score(sp)
    assert s == 50, f"Expected 50, got {s}"

def test_stability_no_data():
    sp = make_scored(apy_30d_avg=0.0, apy_30d_std=0.0)
    s = _calc_stability_score(sp)
    assert s == 50, f"Expected 50 (no data), got {s}"


# ═══════════════════════════════════════════════
# Filter
# ═══════════════════════════════════════════════

def test_filter_flex_only():
    ctx = UserContext(assets=["USDT"], venues=["CEX"], conv_priority="flex")
    products = [
        make_raw(lock_days=0, asset_symbol="USDT"),
        make_raw(source_id="locked", lock_days=30, asset_symbol="USDT"),
    ]
    out = filter_products(products, ctx)
    assert len(out) == 1
    assert out[0].lock_days == 0

def test_filter_removes_sold_out():
    ctx = UserContext(assets=["USDT"], venues=["CEX"])
    products = [make_raw(is_sold_out=True)]
    out = filter_products(products, ctx)
    assert len(out) == 0

def test_filter_removes_apy_outlier():
    ctx = UserContext(assets=["USDT"], venues=["CEX"])
    products = [make_raw(apy_total=500)]  # > 200%
    out = filter_products(products, ctx)
    assert len(out) == 0


# ═══════════════════════════════════════════════
# Anomaly Detection
# ═══════════════════════════════════════════════

def test_anomaly_apy_outlier():
    products = [
        make_scored(source_id="a", effective_apy=5.0),
        make_scored(source_id="b", effective_apy=6.0),
        make_scored(source_id="c", effective_apy=7.0),
        make_scored(source_id="outlier", effective_apy=25.0),
    ]
    out = detect_anomalies(products)
    outlier = [p for p in out if p.source_id == "outlier"][0]
    assert "APY_OUTLIER" in outlier.anomaly_flags

def test_anomaly_declining():
    sp = make_scored(apy_7d_trend=-3.0)
    out = detect_anomalies([sp])
    assert "APY_DECLINING" in out[0].anomaly_flags

def test_anomaly_reward_dependency():
    sp = make_scored(reward_dependency=0.8)
    out = detect_anomalies([sp])
    assert "HIGH_REWARD_DEPENDENCY" in out[0].anomaly_flags


# ═══════════════════════════════════════════════
# Ranking
# ═══════════════════════════════════════════════

def test_rank_order():
    a = make_scored(source_id="a", composite_score=90)
    b = make_scored(source_id="b", composite_score=85)
    c = make_scored(source_id="c", composite_score=95)
    out = rank([a, b, c])
    assert out[0].source_id == "c"
    assert out[0].rank == 1
    assert out[2].rank == 3


# ═══════════════════════════════════════════════
# Run all
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  ✓ {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  ✗ {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ {t.__name__}: EXCEPTION {e}")
            failed += 1

    print(f"\n{'='*40}")
    print(f"  {passed} passed, {failed} failed, {passed+failed} total")
    if failed:
        sys.exit(1)
