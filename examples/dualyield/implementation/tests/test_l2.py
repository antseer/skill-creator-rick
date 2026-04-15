"""
L2 Compute 单元测试 — 21 个测试覆盖所有核心算法
"""
import sys, os, math, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from implementation.pipeline.l2_compute.compute import (
    calc_ma, calc_rsi, calc_macd, calc_hist_vol,
    find_sr_levels, touch_prob, score_product,
    filter_by_risk, filter_by_intent, detect_anomalies, rank_and_select,
    run_ta, _norm_cdf
)
from implementation.pipeline.l2_compute.schema import (
    UserContext, TAResult, ScoredProduct, SRLevel,
    Intent, RiskLevel
)


class TestNormCDF(unittest.TestCase):
    def test_zero(self):
        self.assertAlmostEqual(_norm_cdf(0), 0.5, places=4)
    def test_large_positive(self):
        self.assertAlmostEqual(_norm_cdf(3.0), 0.9987, places=3)
    def test_large_negative(self):
        self.assertAlmostEqual(_norm_cdf(-3.0), 0.0013, places=3)
    def test_symmetry(self):
        self.assertAlmostEqual(_norm_cdf(1.5) + _norm_cdf(-1.5), 1.0, places=4)


class TestMA(unittest.TestCase):
    def test_exact(self):
        data = list(range(1, 21))  # 1..20
        self.assertAlmostEqual(calc_ma(data, 5), 18.0)  # avg(16..20)
    def test_short_data(self):
        self.assertAlmostEqual(calc_ma([10, 20], 20), 15.0)
    def test_empty(self):
        self.assertEqual(calc_ma([], 20), 0.0)


class TestRSI(unittest.TestCase):
    def test_all_up(self):
        prices = [100 + i for i in range(20)]
        rsi = calc_rsi(prices, 14)
        self.assertEqual(rsi, 100.0)

    def test_all_down(self):
        prices = [200 - i for i in range(20)]
        rsi = calc_rsi(prices, 14)
        self.assertEqual(rsi, 0.0)

    def test_flat_returns_neutral(self):
        """FIX验证: 全部持平应返回50 (中性)"""
        prices = [100.0] * 20
        rsi = calc_rsi(prices, 14)
        self.assertEqual(rsi, 50.0)

    def test_insufficient_data(self):
        self.assertEqual(calc_rsi([100, 101], 14), 50.0)


class TestMACD(unittest.TestCase):
    def test_uptrend(self):
        prices = [100 + i * 0.5 for i in range(40)]
        ml, ms, mh = calc_macd(prices)
        self.assertGreater(ml, 0)  # EMA12 > EMA26 in uptrend

    def test_short_data(self):
        ml, ms, mh = calc_macd([100, 101, 102])
        self.assertEqual(ml, 0.0)


class TestHistVol(unittest.TestCase):
    def test_constant_price(self):
        """恒定价格 → 波动率为0"""
        vol = calc_hist_vol([100.0] * 100, 365)
        self.assertEqual(vol, 0.0)

    def test_known_vol(self):
        """
        FIX验证: 生成已知波动率的序列，验证恢复精度
        用固定 seed 的 GBM: S_{t+1} = S_t * exp((σ²/2)dt + σ*sqrt(dt)*Z)
        target σ = 0.60 年化, 日线
        """
        import random
        random.seed(42)
        target_vol = 0.60
        dt = 1 / 365
        prices = [100000.0]
        for _ in range(500):  # 500天足够收敛
            z = random.gauss(0, 1)
            ret = -0.5 * target_vol**2 * dt + target_vol * math.sqrt(dt) * z
            prices.append(prices[-1] * math.exp(ret))
        measured = calc_hist_vol(prices, 365)
        # 500 samples, expect within 15% relative error
        self.assertAlmostEqual(measured, target_vol, delta=target_vol * 0.15)

    def test_hourly_annualization(self):
        """1h蜡烛用8760年化"""
        import random
        random.seed(123)
        target_vol = 0.80
        dt = 1 / 8760
        prices = [50000.0]
        for _ in range(2000):
            z = random.gauss(0, 1)
            ret = -0.5 * target_vol**2 * dt + target_vol * math.sqrt(dt) * z
            prices.append(prices[-1] * math.exp(ret))
        measured = calc_hist_vol(prices, 8760)
        self.assertAlmostEqual(measured, target_vol, delta=target_vol * 0.15)


class TestTouchProb(unittest.TestCase):
    def test_at_spot(self):
        """执行价=现价 → P=1"""
        self.assertAlmostEqual(touch_prob(100000, 100000, 0.6, 7), 1.0)

    def test_far_strike_low_prob(self):
        """
        FIX验证: BTC=100000, K=120000(+20%), σ=0.6, T=7天
        |ln(120000/100000)| = 0.1823
        σ√T = 0.6*√(7/365) = 0.0831
        d = 0.1823/0.0831 = 2.193
        P = 2*Φ(-2.193) ≈ 0.028
        """
        p = touch_prob(100000, 120000, 0.6, 7)
        self.assertLess(p, 0.05)
        self.assertGreater(p, 0.01)

    def test_below_barrier(self):
        """
        FIX验证: K=80000(-20%), 同参数
        |ln(80000/100000)| = 0.2231
        d = 0.2231/0.0831 = 2.684
        P = 2*Φ(-2.684) ≈ 0.007
        """
        p = touch_prob(100000, 80000, 0.6, 7)
        self.assertLess(p, 0.03)
        self.assertGreater(p, 0.001)

    def test_high_vol_increases_prob(self):
        p_low = touch_prob(100000, 110000, 0.3, 7)
        p_high = touch_prob(100000, 110000, 0.9, 7)
        self.assertGreater(p_high, p_low)

    def test_longer_duration_increases_prob(self):
        p_short = touch_prob(100000, 110000, 0.6, 3)
        p_long = touch_prob(100000, 110000, 0.6, 30)
        self.assertGreater(p_long, p_short)

    def test_zero_vol(self):
        self.assertEqual(touch_prob(100000, 110000, 0, 7), 0.0)

    def test_zero_duration(self):
        self.assertEqual(touch_prob(100000, 110000, 0.6, 0), 0.0)


class TestSRLevels(unittest.TestCase):
    def test_finds_resistance(self):
        # 在 105000 附近有 3 次高点
        highs = [100000]*5 + [105000, 100500, 105200, 100300, 104800] + [100000]*5
        lows = [99000]*15
        levels = find_sr_levels(highs, lows, tolerance_pct=0.015, min_touches=2)
        resistance = [l for l in levels if l.kind == "resistance"]
        self.assertGreater(len(resistance), 0)

    def test_empty_on_short_data(self):
        self.assertEqual(find_sr_levels([100]*3, [99]*3), [])


class TestScoring(unittest.TestCase):
    def _make_ta(self):
        return TAResult(current_price=100000, ma20=99000, ma60=97000, ma120=95000,
                        rsi14=55, macd_line=100, macd_signal=50, macd_hist=50,
                        hist_vol_annual=0.6, trend="bullish",
                        sr_levels=[SRLevel(price=110000, strength=3, kind="resistance")])

    def test_high_apr_scores_higher(self):
        ta = self._make_ta()
        ctx = UserContext()
        s1 = score_product("a","binance","cex","BTC","sell_high",115000,7,0.40,100,None,100000,0.6,ta,ctx,1)
        s2 = score_product("b","binance","cex","BTC","sell_high",115000,7,0.10,100,None,100000,0.6,ta,ctx,1)
        self.assertGreater(s1.score, s2.score)

    def test_tier1_bonus(self):
        ta = self._make_ta()
        ctx = UserContext()
        s1 = score_product("a","binance","cex","BTC","sell_high",115000,7,0.20,100,None,100000,0.6,ta,ctx,1)
        s3 = score_product("b","ribbon","defi","BTC","sell_high",115000,7,0.20,100,None,100000,0.6,ta,ctx,3)
        self.assertGreater(s1.score, s3.score)


class TestFiltersAndRank(unittest.TestCase):
    def _make_products(self):
        return [
            ScoredProduct("a","binance","cex","BTC","sell_high",110000,7,0.30,100,None,0.10,0.04,False,None,0.8),
            ScoredProduct("b","okx","cex","BTC","sell_high",112000,7,0.25,100,None,0.12,0.12,False,None,0.6),
            ScoredProduct("c","bybit","cex","BTC","buy_low",90000,7,0.20,100,None,0.10,0.03,False,None,0.7),
        ]

    def test_filter_risk_conservative(self):
        prods = self._make_products()
        filtered = filter_by_risk(prods, RiskLevel.CONSERVATIVE)
        for p in filtered:
            self.assertLessEqual(p.touch_prob, 0.05)

    def test_filter_intent_buy_dip(self):
        prods = self._make_products()
        filtered = filter_by_intent(prods, Intent.BUY_DIP)
        for p in filtered:
            self.assertEqual(p.side, "buy_low")

    def test_rank_order(self):
        prods = self._make_products()
        top = rank_and_select(prods, 2)
        self.assertEqual(len(top), 2)
        self.assertEqual(top[0].rank, 1)
        self.assertGreaterEqual(top[0].score, top[1].score)


class TestAnomalyDetection(unittest.TestCase):
    def test_apr_outlier(self):
        prods = [
            ScoredProduct("a","x","cex","BTC","sell_high",110000,7,0.10,100,None,0.1,0.05,False,None,0.5),
            ScoredProduct("b","y","cex","BTC","sell_high",111000,7,0.12,100,None,0.1,0.05,False,None,0.5),
            ScoredProduct("d","w","cex","BTC","sell_high",111500,7,0.11,100,None,0.1,0.05,False,None,0.5),
            ScoredProduct("e","v","cex","BTC","sell_high",111800,7,0.13,100,None,0.1,0.05,False,None,0.5),
            ScoredProduct("f","u","cex","BTC","sell_high",112000,7,0.09,100,None,0.1,0.05,False,None,0.5),
            ScoredProduct("g","t","cex","BTC","sell_high",112200,7,0.11,100,None,0.1,0.05,False,None,0.5),
            ScoredProduct("h","s","cex","BTC","sell_high",112500,7,0.10,100,None,0.1,0.05,False,None,0.5),
            ScoredProduct("c","z","cex","BTC","sell_high",113000,7,0.80,100,None,0.1,0.05,False,None,0.5),
        ]
        detect_anomalies(prods)
        self.assertIn("APR_OUTLIER", prods[7].anomaly_flags)

    def test_near_expiry(self):
        prods = [
            ScoredProduct("a","x","cex","BTC","sell_high",110000,1,0.10,100,None,0.1,0.05,False,None,0.5),
            ScoredProduct("b","y","cex","BTC","sell_high",111000,7,0.12,100,None,0.1,0.05,False,None,0.5),
            ScoredProduct("c","z","cex","BTC","sell_high",112000,14,0.15,100,None,0.1,0.05,False,None,0.5),
        ]
        detect_anomalies(prods)
        self.assertIn("NEAR_EXPIRY", prods[0].anomaly_flags)


if __name__ == "__main__":
    unittest.main()
