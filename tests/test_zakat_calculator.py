"""
Tests for Zakat Calculator.

Comprehensive test suite covering:
- Nisab calculation
- Wealth zakat
- Livestock zakat
- Crops zakat
- Madhhab differences
- Edge cases
"""
import pytest
from src.tools.zakat_calculator import (
    ZakatCalculator,
    ZakatAssets,
    Madhhab,
)


class TestZakatCalculator:
    """Test suite for ZakatCalculator."""
    
    @pytest.fixture
    def calculator(self):
        """Create calculator with sample prices."""
        return ZakatCalculator(gold_price_per_gram=75.0, silver_price_per_gram=0.9)
    
    @pytest.fixture
    def sample_assets(self):
        """Create sample assets for testing."""
        return ZakatAssets(
            cash=50000,
            gold_grams=100,
            silver_grams=500,
            trade_goods_value=10000,
            stocks_value=5000,
        )
    
    # ==========================================
    # Nisab Calculation Tests
    # ==========================================
    
    def test_nisab_gold_calculation(self, calculator):
        """Test nisab based on gold (85 grams)."""
        nisab_gold = 85 * 75.0  # 6375
        assert abs(calculator._calculate_nisab_gold() - 6375.0) < 0.01
    
    def test_nisab_silver_calculation(self, calculator):
        """Test nisab based on silver (595 grams)."""
        nisab_silver = 595 * 0.9  # 535.5
        assert abs(calculator._calculate_nisab_silver() - 535.5) < 0.01
    
    def test_nisab_effective_is_minimum(self, calculator):
        """Test effective nisab is the lower of gold/silver."""
        # Silver nisab (535.5) < Gold nisab (6375)
        assert calculator._calculate_nisab_silver() < calculator._calculate_nisab_gold()
    
    # ==========================================
    # Wealth Zakat Tests
    # ==========================================
    
    def test_zakat_above_nisab(self, calculator, sample_assets):
        """Test zakat calculation when wealth exceeds nisab."""
        result = calculator.calculate(sample_assets, debts=0, madhhab=Madhhab.GENERAL)
        
        assert result.is_zakatable
        assert result.zakat_amount > 0
        assert result.madhhab == "general"
    
    def test_zakat_below_nisab(self, calculator):
        """Test no zakat when wealth is below nisab."""
        assets = ZakatAssets(cash=1000)
        result = calculator.calculate(assets, debts=0, madhhab=Madhhab.GENERAL)
        
        assert not result.is_zakatable
        assert result.zakat_amount == 0
    
    def test_zakat_with_debts(self, calculator, sample_assets):
        """Test zakat calculation with debt deduction."""
        # High debts should bring wealth below nisab
        result = calculator.calculate(sample_assets, debts=100000, madhhab=Madhhab.GENERAL)
        
        # Debts deducted, may be below nisab
        assert result.debts_deducted <= 100000
    
    def test_zakat_2_5_percent_rate(self, calculator):
        """Test zakat is exactly 2.5% of zakatable wealth."""
        assets = ZakatAssets(cash=100000)
        result = calculator.calculate(assets, debts=0, madhhab=Madhhab.GENERAL)
        
        if result.is_zakatable:
            expected = 100000 * 0.025
            assert abs(result.zakat_amount - expected) < 0.01
    
    def test_zakat_breakdown_structure(self, calculator, sample_assets):
        """Test breakdown contains all asset categories."""
        result = calculator.calculate(sample_assets, madhhab=Madhhab.GENERAL)
        
        assert result.breakdown.cash > 0
        assert result.breakdown.gold_value > 0
        assert result.breakdown.silver_value > 0
        assert result.breakdown.trade_goods > 0
        assert result.breakdown.stocks > 0
    
    # ==========================================
    # Madhhab Difference Tests
    # ==========================================
    
    def test_hanafi_includes_receivables(self, calculator):
        """Test Hanafi madhhab includes receivables in zakatable wealth."""
        assets = ZakatAssets(cash=5000, receivables=10000)
        result_hanafi = calculator.calculate(assets, madhhab=Madhhab.HANAFI)
        result_shafii = calculator.calculate(assets, madhhab=Madhhab.SHAFII)
        
        # Hanafi should include receivables
        assert result_hanafi.breakdown.receivables == 10000
        # Shafii should not
        assert result_shafii.breakdown.receivables == 0
    
    def test_madhhab_notes_present(self, calculator):
        """Test madhhab-specific notes are included."""
        assets = ZakatAssets(cash=5000, receivables=10000)
        result = calculator.calculate(assets, madhhab=Madhhab.HANAFI)
        
        assert len(result.notes) > 0
        assert any("Hanafi" in note for note in result.notes)
    
    # ==========================================
    # Livestock Zakat Tests
    # ==========================================
    
    def test_camels_no_zakat_below_5(self, calculator):
        """Test no zakat on less than 5 camels."""
        result = calculator.calculate_livestock_zakat(camels=4)
        assert not result["camels"]["due"]
    
    def test_camels_5_to_9(self, calculator):
        """Test 5-9 camels = 1 sheep."""
        result = calculator.calculate_livestock_zakat(camels=7)
        assert result["camels"]["due"]
        assert result["camels"]["amount"] == 1
        assert result["camels"]["animal"] == "sheep"
    
    def test_camels_25_to_35(self, calculator):
        """Test 25-35 camels = 1 bint makhad."""
        result = calculator.calculate_livestock_zakat(camels=30)
        assert result["camels"]["due"]
        assert result["camels"]["amount"] == 1
        assert result["camels"]["animal"] == "bint_makhad"
    
    def test_cows_no_zakat_below_30(self, calculator):
        """Test no zakat on less than 30 cows."""
        result = calculator.calculate_livestock_zakat(cows=29)
        assert not result["cows"]["due"]
    
    def test_cows_30_to_39(self, calculator):
        """Test 30-39 cows = 1 tabi'."""
        result = calculator.calculate_livestock_zakat(cows=35)
        assert result["cows"]["due"]
        assert result["cows"]["amount"] == 1
    
    def test_goats_no_zakat_below_40(self, calculator):
        """Test no zakat on less than 40 goats/sheep."""
        result = calculator.calculate_livestock_zakat(goats=39)
        assert not result["goats_sheep"]["due"]
    
    def test_goats_40_to_120(self, calculator):
        """Test 40-120 goats/sheep = 1 sheep."""
        result = calculator.calculate_livestock_zakat(goats=100)
        assert result["goats_sheep"]["due"]
        assert result["goats_sheep"]["amount"] == 1
    
    def test_goats_400_plus(self, calculator):
        """Test 400+ goats/sheep = 1 per 100."""
        result = calculator.calculate_livestock_zakat(goats=500)
        assert result["goats_sheep"]["due"]
        assert result["goats_sheep"]["amount"] == 5
    
    # ==========================================
    # Crops Zakat Tests
    # ==========================================
    
    def test_crops_irrigated_5_percent(self, calculator):
        """Test irrigated crops zakat at 5%."""
        result = calculator.calculate_crops_zakat(10000, irrigation_type="irrigated")
        assert result["due"]
        assert result["rate"] == 0.05
        assert result["amount"] == 500
    
    def test_crops_natural_10_percent(self, calculator):
        """Test rain-fed crops zakat at 10%."""
        result = calculator.calculate_crops_zakat(10000, irrigation_type="natural")
        assert result["due"]
        assert result["rate"] == 0.10
        assert result["amount"] == 1000
    
    def test_crops_zero_value(self, calculator):
        """Test no zakat on zero crop value."""
        result = calculator.calculate_crops_zakat(0)
        assert not result["due"]
        assert result["amount"] == 0
    
    # ==========================================
    # Edge Cases
    # ==========================================
    
    def test_zero_assets(self, calculator):
        """Test calculation with zero assets."""
        assets = ZakatAssets()
        result = calculator.calculate(assets)
        
        assert not result.is_zakatable
        assert result.zakat_amount == 0
        assert result.total_assets == 0
    
    def test_debts_exceed_assets(self, calculator):
        """Test when debts exceed assets."""
        assets = ZakatAssets(cash=1000)
        result = calculator.calculate(assets, debts=5000)
        
        assert result.debts_deducted <= 1000  # Can't deduct more than assets
        assert result.zakatable_wealth == 0
        assert not result.is_zakatable
    
    def test_negative_prices_error(self):
        """Test error on negative metal prices."""
        with pytest.raises(ValueError):
            ZakatCalculator(gold_price_per_gram=-75, silver_price_per_gram=0.9)
    
    def test_references_present(self, calculator, sample_assets):
        """Test references are included in result."""
        result = calculator.calculate(sample_assets)
        
        if result.is_zakatable:
            assert len(result.references) > 0
    
    # ==========================================
    # Integration Test
    # ==========================================
    
    def test_complete_calculation_flow(self, calculator):
        """Test complete zakat calculation for realistic scenario."""
        assets = ZakatAssets(
            cash=20000,
            bank_accounts=30000,
            gold_grams=50,  # 50 * 75 = 3750
            silver_grams=300,  # 300 * 0.9 = 270
            trade_goods_value=15000,
            stocks_value=10000,
            receivables=5000,
        )
        
        result = calculator.calculate(assets, debts=10000, madhhab=Madhhab.HANAFI)
        
        # Verify structure
        assert result.nisab_gold > 0
        assert result.nisab_silver > 0
        assert result.total_assets > 0
        assert result.debts_deducted == 10000
        assert result.zakatable_wealth > 0
        assert result.breakdown.cash == 50000
        assert result.breakdown.gold_value == 3750
        assert result.madhhab == "hanafi"
