"""
Zakat Calculator for Burhan Islamic QA system.

Deterministic calculator for Zakat calculations based on Islamic jurisprudence rules.
Supports multiple asset types, madhhab differences, and specialized rates for
livestock and agricultural products.

Based on Fanar-Sadiq architecture: No LLM involvement for calculations.
"""
from dataclasses import dataclass, field
from enum import Enum

from src.config.logging_config import get_logger

logger = get_logger()


class ZakatType(str, Enum):
    """Types of zakat calculations."""
    WEALTH = "wealth"
    GOLD = "gold"
    SILVER = "silver"
    TRADE_GOODS = "trade_goods"
    STOCKS = "stocks"
    LIVESTOCK = "livestock"
    CROPS = "crops"
    MINERALS = "minerals"


class Madhhab(str, Enum):
    """Islamic schools of jurisprudence."""
    HANAFI = "hanafi"
    MALIKI = "maliki"
    SHAFII = "shafii"
    HANBALI = "hanbali"
    GENERAL = "general"


@dataclass
class ZakatAssets:
    """
    User's zakatable assets.

    All values should be in the same currency (e.g., USD, QAR).
    """
    cash: float = 0.0
    bank_accounts: float = 0.0
    gold_grams: float = 0.0
    silver_grams: float = 0.0
    trade_goods_value: float = 0.0
    stocks_value: float = 0.0
    receivables: float = 0.0  # Money owed to user
    livestock_value: float = 0.0
    crops_value: float = 0.0
    minerals_value: float = 0.0


@dataclass
class ZakatBreakdown:
    """Detailed breakdown of zakat calculation."""
    cash: float = 0.0
    gold_value: float = 0.0
    silver_value: float = 0.0
    trade_goods: float = 0.0
    stocks: float = 0.0
    receivables: float = 0.0
    other: float = 0.0


@dataclass
class ZakatResult:
    """
    Complete zakat calculation result.

    Contains all information needed to present the calculation
    to the user with transparency and scholarly references.
    """
    # Nisab calculation
    nisab_gold: float  # Nisab based on gold (85g)
    nisab_silver: float  # Nisab based on silver (595g)
    nisab_effective: float  # Lower of the two (benefits poor)

    # Asset calculation
    total_assets: float
    debts_deducted: float
    zakatable_wealth: float

    # Result
    is_zakatable: bool
    zakat_amount: float
    breakdown: ZakatBreakdown

    # Metadata
    madhhab: str
    gold_price_per_gram: float
    silver_price_per_gram: float
    notes: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)


class ZakatCalculator:
    """
    Deterministic zakat calculator implementing fiqh rules.

    This calculator:
    - Uses fixed formulas (no LLM generation)
    - Supports madhhab differences
    - Handles multiple asset types
    - Provides transparent breakdowns

    Usage:
        calculator = ZakatCalculator(gold_price=75, silver_price=0.9)
        assets = ZakatAssets(cash=50000, gold_grams=100)
        result = calculator.calculate(assets, debts=5000, madhhab="shafii")
    """

    # ==========================================
    # Constants from Islamic jurisprudence
    # ==========================================
    GOLD_NISAB_GRAMS = 85.0
    SILVER_NISAB_GRAMS = 595.0
    WEALTH_ZAKAT_RATE = 0.025  # 2.5%
    MINERALS_ZAKAT_RATE = 0.025  # 2.5% (rikaz: 20%)
    CROP_ZAKAT_RATE_IRRIGATED = 0.05  # 5% (with irrigation cost)
    CROP_ZAKAT_RATE_NATURAL = 0.10  # 10% (natural rainfall)

    def __init__(self, gold_price_per_gram: float, silver_price_per_gram: float):
        """
        Initialize calculator with current metal prices.

        Args:
            gold_price_per_gram: Current price of 1 gram of gold
            silver_price_per_gram: Current price of 1 gram of silver
        """
        if gold_price_per_gram <= 0 or silver_price_per_gram <= 0:
            raise ValueError("Metal prices must be positive")

        self.gold_price = gold_price_per_gram
        self.silver_price = silver_price_per_gram

        logger.info(
            "zakat.calculator_initialized",
            gold_price=gold_price_per_gram,
            silver_price=silver_price_per_gram,
            nisab_gold=self._calculate_nisab_gold(),
            nisab_silver=self._calculate_nisab_silver()
        )

    def calculate(
        self,
        assets: ZakatAssets,
        debts: float = 0.0,
        madhhab: Madhhab = Madhhab.GENERAL,
        crop_irrigation_type: str = "irrigated"
    ) -> ZakatResult:
        """
        Calculate zakat for a complete financial picture.

        Args:
            assets: All zakatable assets
            debts: Outstanding debts to deduct
            madhhab: School of jurisprudence for rule differences
            crop_irrigation_type: "irrigated" (5%) or "natural" (10%)

        Returns:
            Complete zakat calculation result with breakdown
        """
        # Step 1: Calculate nisab thresholds
        nisab_gold = self._calculate_nisab_gold()
        nisab_silver = self._calculate_nisab_silver()
        nisab_effective = min(nisab_gold, nisab_silver)

        # Step 2: Calculate asset values
        breakdown = self._calculate_asset_values(assets, madhhab)
        total_assets = sum([
            breakdown.cash,
            breakdown.gold_value,
            breakdown.silver_value,
            breakdown.trade_goods,
            breakdown.stocks,
            breakdown.receivables,
            breakdown.other,
        ])

        # Step 3: Deduct debts
        debts_deducted = min(debts, total_assets)  # Can't deduct more than assets
        zakatable_wealth = max(0, total_assets - debts_deducted)

        # Step 4: Check against nisab
        is_zakatable = zakatable_wealth >= nisab_effective

        # Step 5: Calculate zakat amount
        zakat_amount = 0.0
        notes = []
        references = []

        if is_zakatable:
            zakat_amount = round(zakatable_wealth * self.WEALTH_ZAKAT_RATE, 2)
            notes.append(
                f"Your wealth ({zakatable_wealth:,.2f}) exceeds the nisab threshold "
                f"({nisab_effective:,.2f}). Zakat is due at 2.5%."
            )
            references.append("Quran 9:103 - Take from their wealth a charity")
            references.append("Hadith: No zakat is due until one year passes (Tirmidhi)")
        else:
            notes.append(
                f"Your wealth ({zakatable_wealth:,.2f}) is below the nisab threshold "
                f"({nisab_effective:,.2f}). No zakat is due."
            )

        # Madhhab-specific notes
        if madhhab == Madhhab.HANAFI and assets.receivables > 0:
            notes.append(
                "Hanafi madhhab: Receivables are included in zakatable wealth. "
                "Pay zakat on them when received if not paid earlier."
            )
        elif madhhab in [Madhhab.SHAFII, Madhhab.MALIKI] and assets.receivables > 0:
            notes.append(
                f"{madhhab.value.capitalize()} madhhab: Receivables are not included "
                "until actually received. Pay zakat for past years when collected."
            )

        # Build result
        result = ZakatResult(
            nisab_gold=nisab_gold,
            nisab_silver=nisab_silver,
            nisab_effective=nisab_effective,
            total_assets=total_assets,
            debts_deducted=debts_deducted,
            zakatable_wealth=round(zakatable_wealth, 2),
            is_zakatable=is_zakatable,
            zakat_amount=zakat_amount,
            breakdown=breakdown,
            madhhab=madhhab.value,
            gold_price_per_gram=self.gold_price,
            silver_price_per_gram=self.silver_price,
            notes=notes,
            references=references
        )

        logger.info(
            "zakat.calculated",
            is_zakatable=is_zakatable,
            zakat_amount=zakat_amount,
            madhhab=madhhab.value
        )

        return result

    def calculate_livestock_zakat(
        self,
        camels: int = 0,
        cows: int = 0,
        goats: int = 0,
        sheep: int = 0
    ) -> dict:
        """
        Calculate zakat for livestock based on specific hadith rates.

        These are fixed rates from prophetic traditions, not percentages.

        Args:
            camels: Number of camels
            cows: Number of cows/buffaloes
            goats: Number of goats
            sheep: Number of sheep

        Returns:
            Dictionary with zakat obligations for each animal type
        """
        result = {
            "camels": self._calculate_camels_zakat(camels),
            "cows": self._calculate_cows_zakat(cows),
            "goats_sheep": self._calculate_goats_sheep_zakat(goats + sheep),
        }

        total_due = []
        for _animal_type, obligation in result.items():
            if obligation["due"]:
                total_due.append(f"{obligation['amount']} {obligation['animal']}")

        result["summary"] = ", ".join(total_due) if total_due else "No zakat due"
        result["references"] = [
            "Hadith: Zakat rates for livestock are specified in Sahih Bukhari",
            "Book: Kitab Az-Zakat, Hadith 1454"
        ]

        return result

    def calculate_crops_zakat(
        self,
        total_value: float,
        irrigation_type: str = "irrigated"
    ) -> dict:
        """
        Calculate zakat for agricultural products.

        Args:
            total_value: Total value of crops
            irrigation_type: "irrigated" (costs incurred) or "natural" (rain-fed)

        Returns:
            Dictionary with zakat obligation
        """
        if total_value <= 0:
            return {"due": False, "amount": 0, "rate": 0}

        if irrigation_type == "natural":
            rate = self.CROP_ZAKAT_RATE_NATURAL  # 10%
        else:
            rate = self.CROP_ZAKAT_RATE_IRRIGATED  # 5%

        amount = round(total_value * rate, 2)

        return {
            "due": True,
            "amount": amount,
            "rate": rate,
            "irrigation_type": irrigation_type,
            "reference": "Quran 6:141 - He it is who produces gardens... and give its due on the day of harvest"
        }

    # ==========================================
    # Private calculation methods
    # ==========================================

    def _calculate_nisab_gold(self) -> float:
        """Calculate nisab based on gold (85 grams)."""
        return self.GOLD_NISAB_GRAMS * self.gold_price

    def _calculate_nisab_silver(self) -> float:
        """Calculate nisab based on silver (595 grams)."""
        return self.SILVER_NISAB_GRAMS * self.silver_price

    def _calculate_asset_values(
        self,
        assets: ZakatAssets,
        madhhab: Madhhab
    ) -> ZakatBreakdown:
        """Calculate monetary value of all assets."""
        gold_value = assets.gold_grams * self.gold_price
        silver_value = assets.silver_grams * self.silver_price

        # Hanafi includes receivables, others differ
        receivables = assets.receivables if madhhab == Madhhab.HANAFI else 0.0

        return ZakatBreakdown(
            cash=assets.cash + assets.bank_accounts,
            gold_value=gold_value,
            silver_value=silver_value,
            trade_goods=assets.trade_goods_value,
            stocks=assets.stocks_value,
            receivables=receivables,
            other=assets.livestock_value + assets.crops_value + assets.minerals_value
        )

    def _calculate_camels_zakat(self, count: int) -> dict:
        """
        Calculate zakat for camels based on hadith.

        Rates from Sahih Bukhari:
        - 1-4: No zakat
        - 5-9: 1 sheep
        - 10-14: 2 sheep
        - 15-19: 3 sheep
        - 20-24: 4 sheep
        - 25-35: 1 bint makhad (1-year-old she-camel)
        - 36-45: 1 bint labun (2-year-old she-camel)
        - 46-60: 1 hiqqah (3-year-old she-camel)
        - 61-75: 1 jadha'ah (4-year-old she-camel)
        - 76-90: 2 bint labun
        - 91-120: 2 hiqqah
        - 121+: 1 bint labun per 40, 1 hiqqah per 50
        """
        if count < 5:
            return {"due": False, "amount": 0, "animal": "sheep"}

        rates = [
            (5, 9, 1, "sheep"),
            (10, 14, 2, "sheep"),
            (15, 19, 3, "sheep"),
            (20, 24, 4, "sheep"),
            (25, 35, 1, "bint_makhad"),
            (36, 45, 1, "bint_labun"),
            (46, 60, 1, "hiqqah"),
            (61, 75, 1, "jadha'ah"),
            (76, 90, 2, "bint_labun"),
            (91, 120, 2, "hiqqah"),
        ]

        for min_count, max_count, amount, animal in rates:
            if min_count <= count <= max_count:
                return {"due": True, "amount": amount, "animal": animal}

        # 121+ camels
        if count >= 121:
            return {
                "due": True,
                "amount": "1 bint labun per 40, 1 hiqqah per 50",
                "animal": "mixed"
            }

        return {"due": False, "amount": 0, "animal": "sheep"}

    def _calculate_cows_zakat(self, count: int) -> dict:
        """
        Calculate zakat for cows/buffaloes.

        Rates:
        - 1-29: No zakat
        - 30-39: 1 tabi' or tabi'ah (1-year-old)
        - 40-59: 1 musinnah (2-year-old)
        - 60+: 2 tabi' or 1 musinnah + 1 tabi'
        """
        if count < 30:
            return {"due": False, "amount": 0, "animal": "cow"}
        elif count <= 39:
            return {"due": True, "amount": 1, "animal": "tabi'"}
        elif count <= 59:
            return {"due": True, "amount": 1, "animal": "musinnah"}
        else:
            return {"due": True, "amount": "1 tabi' per 30, 1 musinnah per 40", "animal": "mixed"}

    def _calculate_goats_sheep_zakat(self, count: int) -> dict:
        """
        Calculate zakat for goats/sheep.

        Rates:
        - 1-39: No zakat
        - 40-120: 1 sheep
        - 121-200: 2 sheep
        - 201-399: 3 sheep
        - 400+: 1 sheep per 100
        """
        if count < 40:
            return {"due": False, "amount": 0, "animal": "sheep"}
        elif count <= 120:
            return {"due": True, "amount": 1, "animal": "sheep"}
        elif count <= 200:
            return {"due": True, "amount": 2, "animal": "sheep"}
        elif count <= 399:
            return {"due": True, "amount": 3, "animal": "sheep"}
        else:
            return {"due": True, "amount": count // 100, "animal": "sheep"}
