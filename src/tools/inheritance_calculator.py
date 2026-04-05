"""
Inheritance Calculator for Athar Islamic QA system.

Deterministic calculator for Islamic inheritance distribution (fara'id) based on
Quranic verses and prophetic traditions. Implements fixed shares (furood),
residuary (asabah), 'awl (proportional reduction), and radd (redistribution).

Supports madhhab differences for disputed cases.
Based on Fanar-Sadiq architecture: No LLM involvement for calculations.
"""

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Optional

from src.config.logging_config import get_logger

logger = get_logger()


@dataclass
class Heirs:
    """
    Definition of surviving heirs.

    Boolean flags for single-presence heirs (husband, father, mother).
    Integer counts for multiple-possible heirs (wives, sons, daughters).
    """

    # Spouse
    husband: bool = False
    wife_count: int = 0

    # Parents
    father: bool = False
    mother: bool = False

    # Grandparents
    paternal_grandfather: bool = False

    # Descendants
    sons: int = 0
    daughters: int = 0
    grandsons: int = 0  # Son's sons

    # Siblings
    full_brothers: int = 0
    full_sisters: int = 0
    paternal_half_brothers: int = 0
    paternal_half_sisters: int = 0
    maternal_brothers: int = 0
    maternal_sisters: int = 0

    # Others
    uterine_brothers: int = 0  # Mother's sons (from different father)
    uterine_sisters: int = 0  # Mother's children (from different father)


@dataclass
class InheritanceShare:
    """Share allocation for a single heir or heir group."""

    heir_name: str
    fraction: Fraction
    percentage: float
    amount: float
    basis: str  # "fard", "asabah", "radd", "remainder"
    notes: str = ""


@dataclass
class InheritanceResult:
    """
    Complete inheritance distribution result.

    Contains all information needed to present the distribution
    to the user with transparency and scholarly references.
    """

    # Required fields first (no defaults)
    distribution: list[InheritanceShare]
    total_distributed: float
    remaining: float
    method: str  # "standard", "awl", "radd"
    estate_value: float
    total_heirs: int

    # Optional fields (with defaults)
    school_opinion: Optional[str] = None  # Madhhab-specific note
    notes: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)


class InheritanceCalculator:
    """
    Deterministic inheritance calculator implementing fara'id rules.

    This calculator:
    - Uses exact fraction arithmetic (no floating point errors)
    - Implements furood (fixed shares) from Quran
    - Implements asabah (residuary) from Sunnah
    - Handles 'awl (proportional reduction)
    - Handles radd (redistribution)
    - Supports madhhab differences

    Usage:
        calculator = InheritanceCalculator()
        heirs = Heirs(husband=True, father=True, mother=True, sons=1, daughters=1)
        result = calculator.calculate(100000, heirs, madhhab="shafii")
    """

    # ==========================================
    # Fixed shares (Furood) from Quran
    # ==========================================
    # Husband
    HUSBAND_WITH_DESCENDANTS = Fraction(1, 4)
    HUSBAND_WITHOUT_DESCENDANTS = Fraction(1, 2)

    # Wife
    WIFE_WITH_DESCENDANTS = Fraction(1, 8)
    WIFE_WITHOUT_DESCENDANTS = Fraction(1, 4)

    # Father
    FATHER_WITH_MALE_DESCENDANTS = Fraction(1, 6)

    # Mother
    MOTHER_WITH_SIBLINGS = Fraction(1, 6)
    MOTHER_WITHOUT_SIBLINGS = Fraction(1, 3)

    # Mother (Umariyatan - special case with father + spouse)
    MOTHER_UMARIYATAN = Fraction(1, 3)

    # Paternal Grandfather (same as father when father absent)
    PATERNAL_GRANDFATHER_WITH_MALE_DESCENDANTS = Fraction(1, 6)

    # Daughters
    DAUGHTER_SINGLE = Fraction(1, 2)
    DAUGHTER_MULTIPLE = Fraction(2, 3)

    # Full Sisters (when no descendants or father)
    FULL_SISTER_SINGLE = Fraction(1, 2)
    FULL_SISTER_MULTIPLE = Fraction(2, 3)

    # Paternal Half-Sisters
    PATERNAL_SISTER_SINGLE = Fraction(1, 2)
    PATERNAL_SISTER_MULTIPLE = Fraction(2, 3)

    # Uterine (Maternal) Siblings
    UTERINE_SINGLE = Fraction(1, 6)
    UTERINE_MULTIPLE = Fraction(1, 3)

    def calculate(
        self, estate_value: float, heirs: Heirs, madhhab: str = "general", debts: float = 0.0, wasiyyah: float = 0.0
    ) -> InheritanceResult:
        """
        Calculate inheritance distribution.

        Args:
            estate_value: Total estate value
            heirs: Definition of surviving heirs
            madhhab: School of jurisprudence
            debts: Debts to deduct before distribution
            wasiyyah: Bequest amount (max 1/3 of estate)

        Returns:
            Complete inheritance distribution result
        """
        if estate_value <= 0:
            raise ValueError("Estate value must be positive")

        # Step 1: Deduct debts and bequests (max 1/3)
        net_estate = self._calculate_net_estate(estate_value, debts, wasiyyah)

        # Step 2: Determine who inherits (remove blocked heirs)
        active_heirs = self._remove_blocked_heirs(heirs, madhhab)

        # Step 3: Calculate fixed shares (furood)
        furood_shares = self._calculate_furood(active_heirs)
        total_furood = sum((s.fraction for s in furood_shares), Fraction(0))

        # Step 4: Check for 'awl or radd
        method = "standard"
        distribution = furood_shares[:]

        if total_furood > 1:
            # 'Awl: Proportional reduction
            distribution = self._apply_awl(furood_shares, net_estate)
            method = "awl"
        elif total_furood < 1:
            # Check for asabah (residuary heirs)
            asabah_heirs = self._identify_asabah(active_heirs)

            if asabah_heirs:
                # Give remainder to asabah
                remainder = 1 - total_furood
                asabah_shares = self._calculate_asabah_shares(asabah_heirs, remainder, net_estate)
                distribution.extend(asabah_shares)
            else:
                # Radd: Redistribute to fard heirs (proportional)
                distribution = self._apply_radd(furood_shares, net_estate)
                method = "radd"

        # Step 5: Handle madhhab differences
        school_note = self._get_madhhab_note(madhhab, heirs, distribution)

        # Step 6: Build result
        total_distributed = sum(s.amount for s in distribution)
        remaining = round(net_estate - total_distributed, 2)

        notes = self._generate_notes(heirs, method, madhhab)
        references = self._get_references()

        result = InheritanceResult(
            distribution=distribution,
            total_distributed=round(total_distributed, 2),
            remaining=remaining,
            method=method,
            school_opinion=school_note,
            estate_value=net_estate,
            total_heirs=self._count_heirs(active_heirs),
            notes=notes,
            references=references,
        )

        logger.info(
            "inheritance.calculated",
            estate_value=estate_value,
            net_estate=net_estate,
            method=method,
            heirs_count=self._count_heirs(active_heirs),
        )

        return result

    # ==========================================
    # Private calculation methods
    # ==========================================

    def _calculate_net_estate(self, estate_value: float, debts: float, wasiyyah: float) -> float:
        """Calculate net estate after debts and bequests."""
        # Deduct debts
        net = estate_value - debts

        # Deduct bequests (max 1/3 of remaining)
        max_wasiyyah = net / 3
        actual_wasiyyah = min(wasiyyah, max_wasiyyah)
        net -= actual_wasiyyah

        return max(0, net)

    def _remove_blocked_heirs(self, heirs: Heirs, madhhab: str) -> Heirs:
        """
        Remove heirs who are blocked from inheritance.

        Blocking rules:
        - Son blocks: grandson, full brothers, paternal brothers, maternal brothers
        - Father blocks: paternal grandfather, full brothers, paternal brothers
        - Husband present: no blocking of wife
        """
        has_male_descendant = heirs.sons > 0 or heirs.grandsons > 0
        has_father = heirs.father

        # Create filtered copy
        active = Heirs(
            husband=heirs.husband,
            wife_count=heirs.wife_count,
            father=heirs.father,
            mother=heirs.mother,
            paternal_grandfather=heirs.paternal_grandfather if not has_father else False,
            sons=heirs.sons,
            daughters=heirs.daughters,
            grandsons=heirs.grandsons if not heirs.sons else 0,
            full_brothers=heirs.full_brothers if not has_male_descendant and not has_father else 0,
            full_sisters=heirs.full_sisters,
            paternal_half_brothers=heirs.paternal_half_brothers if not has_male_descendant and not has_father else 0,
            paternal_half_sisters=heirs.paternal_half_sisters,
            maternal_brothers=heirs.maternal_brothers,
            maternal_sisters=heirs.maternal_sisters,
            uterine_brothers=heirs.uterine_brothers,
            uterine_sisters=heirs.uterine_sisters,
        )

        return active

    def _calculate_furood(self, heirs: Heirs) -> list[InheritanceShare]:
        """Calculate fixed shares (furood) for eligible heirs."""
        shares = []
        has_descendants = heirs.sons > 0 or heirs.daughters > 0 or heirs.grandsons > 0
        has_siblings = (
            heirs.full_brothers
            + heirs.full_sisters
            + heirs.paternal_half_brothers
            + heirs.paternal_half_sisters
            + heirs.uterine_brothers
            + heirs.uterine_sisters
        ) >= 2

        # Husband's share
        if heirs.husband:
            fraction = self.HUSBAND_WITH_DESCENDANTS if has_descendants else self.HUSBAND_WITHOUT_DESCENDANTS
            shares.append(
                InheritanceShare(
                    heir_name="Husband", fraction=fraction, percentage=0, amount=0, basis="fard", notes="Quran 4:12"
                )
            )

        # Wife's share
        if heirs.wife_count > 0:
            fraction = self.WIFE_WITH_DESCENDANTS if has_descendants else self.WIFE_WITHOUT_DESCENDANTS
            total_wife_share = fraction * heirs.wife_count
            shares.append(
                InheritanceShare(
                    heir_name=f"Wife{'s' if heirs.wife_count > 1 else ''}",
                    fraction=total_wife_share,
                    percentage=0,
                    amount=0,
                    basis="fard",
                    notes=f"Quran 4:12 (shared among {heirs.wife_count} wife/wives)",
                )
            )

        # Father's share
        if heirs.father:
            if heirs.sons > 0:
                # Father gets 1/6 as fard, remainder as asabah
                fraction = self.FATHER_WITH_MALE_DESCENDANTS
                shares.append(
                    InheritanceShare(
                        heir_name="Father",
                        fraction=fraction,
                        percentage=0,
                        amount=0,
                        basis="fard + asabah",
                        notes="Quran 4:11 (1/6 fard, remainder as asabah)",
                    )
                )
            elif heirs.daughters > 0:
                # Father gets 1/6 as fard
                fraction = self.FATHER_WITH_MALE_DESCENDANTS
                shares.append(
                    InheritanceShare(
                        heir_name="Father", fraction=fraction, percentage=0, amount=0, basis="fard", notes="Quran 4:11"
                    )
                )
            # If no descendants, father gets everything as asabah (handled later)

        # Mother's share
        if heirs.mother:
            # Check for Umariyatan case (father + spouse present)
            is_umariyatan = (
                heirs.father and (heirs.husband or heirs.wife_count > 0) and not has_descendants and not has_siblings
            )

            if is_umariyatan:
                fraction = self.MOTHER_UMARIYATAN
            elif has_siblings:
                fraction = self.MOTHER_WITH_SIBLINGS
            else:
                fraction = self.MOTHER_WITHOUT_SIBLINGS

            shares.append(
                InheritanceShare(
                    heir_name="Mother", fraction=fraction, percentage=0, amount=0, basis="fard", notes="Quran 4:11"
                )
            )

        # Paternal Grandfather's share (when father absent)
        if heirs.paternal_grandfather and not heirs.father:
            if heirs.sons > 0:
                fraction = self.PATERNAL_GRANDFATHER_WITH_MALE_DESCENDANTS
                shares.append(
                    InheritanceShare(
                        heir_name="Paternal Grandfather",
                        fraction=fraction,
                        percentage=0,
                        amount=0,
                        basis="fard",
                        notes="Same ruling as father when father absent",
                    )
                )

        # Daughters' shares
        if heirs.daughters > 0:
            if heirs.sons == 0:
                # Daughters get fard
                if heirs.daughters == 1:
                    fraction = self.DAUGHTER_SINGLE
                    shares.append(
                        InheritanceShare(
                            heir_name="Daughter",
                            fraction=fraction,
                            percentage=0,
                            amount=0,
                            basis="fard",
                            notes="Quran 4:11",
                        )
                    )
                else:
                    fraction = self.DAUGHTER_MULTIPLE
                    shares.append(
                        InheritanceShare(
                            heir_name=f"Daughters ({heirs.daughters})",
                            fraction=fraction,
                            percentage=0,
                            amount=0,
                            basis="fard",
                            notes="Quran 4:11 (shared among daughters)",
                        )
                    )
            # If sons present, daughters become asabah bil-ghayr (handled in asabah)

        # Full sisters (only when no descendants, no father, no full brothers as asabah)
        if heirs.full_sisters > 0 and not has_descendants and not heirs.father and heirs.full_brothers == 0:
            if heirs.full_sisters == 1:
                fraction = self.FULL_SISTER_SINGLE
                shares.append(
                    InheritanceShare(
                        heir_name="Full Sister",
                        fraction=fraction,
                        percentage=0,
                        amount=0,
                        basis="fard",
                        notes="Quran 4:12",
                    )
                )
            else:
                fraction = self.FULL_SISTER_MULTIPLE
                shares.append(
                    InheritanceShare(
                        heir_name=f"Full Sisters ({heirs.full_sisters})",
                        fraction=fraction,
                        percentage=0,
                        amount=0,
                        basis="fard",
                        notes="Quran 4:12",
                    )
                )

        # Uterine (maternal) siblings
        total_uterine = heirs.uterine_brothers + heirs.uterine_sisters
        if total_uterine > 0 and not has_descendants and not heirs.father:
            if total_uterine == 1:
                fraction = self.UTERINE_SINGLE
            else:
                fraction = self.UTERINE_MULTIPLE

            shares.append(
                InheritanceShare(
                    heir_name=f"Uterine Sibling{'s' if total_uterine > 1 else ''}",
                    fraction=fraction,
                    percentage=0,
                    amount=0,
                    basis="fard",
                    notes="Quran 4:12",
                )
            )

        return shares

    def _identify_asabah(self, heirs: Heirs) -> list[tuple[str, int]]:
        """
        Identify residuary heirs (asabah).

        Returns list of (heir_name, count) tuples.
        """
        asabah = []
        has_descendants = heirs.sons > 0 or heirs.daughters > 0

        # Sons (always asabah)
        if heirs.sons > 0:
            asabah.append(("Son", heirs.sons))

        # Father (when no male descendants)
        if heirs.father and not heirs.sons:
            asabah.append(("Father", 1))

        # Paternal Grandfather (when no father, no sons)
        if heirs.paternal_grandfather and not heirs.father and not heirs.sons:
            asabah.append(("Paternal Grandfather", 1))

        # Full brothers (when no descendants, no father, no paternal grandfather)
        if heirs.full_brothers > 0 and not has_descendants and not heirs.father and not heirs.paternal_grandfather:
            asabah.append(("Full Brother", heirs.full_brothers))

        # Paternal half-brothers (when no full brothers)
        if (
            heirs.paternal_half_brothers > 0
            and not has_descendants
            and not heirs.father
            and not heirs.paternal_grandfather
            and heirs.full_brothers == 0
        ):
            asabah.append(("Paternal Half-Brother", heirs.paternal_half_brothers))

        return asabah

    def _calculate_asabah_shares(
        self, asabah_heirs: list[tuple[str, int]], remainder: Fraction, estate_value: float
    ) -> list[InheritanceShare]:
        """Calculate shares for residuary heirs."""
        shares = []

        for heir_name, count in asabah_heirs:
            # Male gets 2x female for sons/daughters
            if "Son" in heir_name or "Daughter" in heir_name:
                # Special case: handled differently
                pass
            else:
                # Equal share for other asabah
                share_per_heir = remainder / count if count > 0 else Fraction(0)
                amount = float(share_per_heir) * estate_value

                shares.append(
                    InheritanceShare(
                        heir_name=f"{heir_name}{'s' if count > 1 else ''}",
                        fraction=share_per_heir * count,
                        percentage=float(share_per_heir * count) * 100,
                        amount=round(amount, 2),
                        basis="asabah",
                        notes="Residuary heir",
                    )
                )

        return shares

    def _apply_awl(self, furood_shares: list[InheritanceShare], estate_value: float) -> list[InheritanceShare]:
        """
        Apply 'awl (proportional reduction).

        When sum of fractions > 1, increase the base proportionally.
        Example: 1/2 + 1/2 + 1/3 = 4/3 → base becomes 13 instead of 12
        """
        total_furood = sum((s.fraction for s in furood_shares), Fraction(0))

        # Increase base to match total
        # If fractions sum to 13/12, new base is 13
        distribution = []
        for share in furood_shares:
            # Scale down proportionally
            scaled_fraction = share.fraction / total_furood
            amount = float(scaled_fraction) * estate_value

            distribution.append(
                InheritanceShare(
                    heir_name=share.heir_name,
                    fraction=scaled_fraction,
                    percentage=float(scaled_fraction) * 100,
                    amount=round(amount, 2),
                    basis="fard ('awl)",
                    notes=f"Reduced proportionally (original: {share.fraction})",
                )
            )

        return distribution

    def _apply_radd(self, furood_shares: list[InheritanceShare], estate_value: float) -> list[InheritanceShare]:
        """
        Apply radd (redistribution).

        When sum of fractions < 1 and no asabah, redistribute remainder
        to fard heirs proportionally (except spouse in some madhhabs).
        """
        total_furood = sum((s.fraction for s in furood_shares), Fraction(0))
        remainder = 1 - total_furood

        distribution = []
        for share in furood_shares:
            # Add proportional share of remainder
            extra = share.fraction / total_furood * remainder
            new_fraction = share.fraction + extra
            amount = float(new_fraction) * estate_value

            distribution.append(
                InheritanceShare(
                    heir_name=share.heir_name,
                    fraction=new_fraction,
                    percentage=float(new_fraction) * 100,
                    amount=round(amount, 2),
                    basis="fard + radd",
                    notes=f"Increased proportionally (original: {share.fraction})",
                )
            )

        return distribution

    def _get_madhhab_note(self, madhhab: str, heirs: Heirs, distribution: list[InheritanceShare]) -> Optional[str]:
        """Get madhhab-specific notes for disputed cases."""
        if madhhab == "hanafi":
            # Hanafi: Maternal siblings can block paternal half-siblings in some cases
            if heirs.maternal_brothers > 0 and heirs.paternal_half_brothers > 0:
                return (
                    "Hanafi opinion: Maternal siblings may affect paternal "
                    "half-sibling inheritance in certain configurations."
                )

        elif madhhab in ["shafii", "maliki", "hanbali"]:
            # Jumhur: Different handling of grandfather + brothers case
            if heirs.paternal_grandfather and (heirs.full_brothers > 0 or heirs.full_sisters > 0):
                return (
                    "Jumhur opinion: Grandfather is treated like father in "
                    "blocking siblings, differing from Hanafi view."
                )

        return None

    def _generate_notes(self, heirs: Heirs, method: str, madhhab: str) -> list[str]:
        """Generate explanatory notes for the distribution."""
        notes = []

        if method == "awl":
            notes.append(
                "'Awl was applied: The sum of fixed shares exceeded the estate, "
                "so all shares were reduced proportionally."
            )
        elif method == "radd":
            notes.append(
                "Radd was applied: There were no residuary heirs, so the remainder "
                "was redistributed to the fixed-share heirs proportionally."
            )

        notes.append(
            "This is a mathematical calculation based on fara'id rules. "
            "Consult a qualified scholar for complex cases or disputes."
        )
        notes.append("Funeral expenses and debts should be paid before distribution.")

        return notes

    def _get_references(self) -> list[str]:
        """Get scholarly references for inheritance rules."""
        return [
            "Quran 4:11-12 - Verses of inheritance (fara'id)",
            "Quran 4:176 - Kalalah inheritance",
            "Sahih Bukhari - Kitab al-Fara'id",
            "Sahih Muslim - Kitab al-Fara'id",
            "Ibn Qudamah - Al-Mughni (Volume 6)",
            "Al-Jaziri - Kitab al-Fiqh 'ala al-Madhahib al-Arba'ah",
        ]

    def _count_heirs(self, heirs: Heirs) -> int:
        """Count total number of individual heirs."""
        count = 0
        count += 1 if heirs.husband else 0
        count += heirs.wife_count
        count += 1 if heirs.father else 0
        count += 1 if heirs.mother else 0
        count += 1 if heirs.paternal_grandfather else 0
        count += heirs.sons
        count += heirs.daughters
        count += heirs.grandsons
        count += heirs.full_brothers
        count += heirs.full_sisters
        count += heirs.paternal_half_brothers
        count += heirs.paternal_half_sisters
        count += heirs.uterine_brothers
        count += heirs.uterine_sisters
        return count
