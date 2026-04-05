"""
Tests for Inheritance Calculator.

Comprehensive test suite covering:
- Fixed shares (furood)
- Residuary (asabah)
- 'Awl (proportional reduction)
- Radd (redistribution)
- Blocked heirs
- Madhhab differences
- Edge cases
- Accuracy verification (sum == estate)
"""
import pytest
from src.tools.inheritance_calculator import (
    InheritanceCalculator,
    Heirs,
)


class TestInheritanceCalculator:
    """Test suite for InheritanceCalculator."""
    
    @pytest.fixture
    def calculator(self):
        """Create calculator instance."""
        return InheritanceCalculator()
    
    # ==========================================
    # Basic Share Tests
    # ==========================================
    
    def test_husband_with_descendants(self, calculator):
        """Test husband gets 1/4 when there are descendants."""
        heirs = Heirs(husband=True, sons=1)
        result = calculator.calculate(100000, heirs)
        
        husband_share = next(s for s in result.distribution if "Husband" in s.heir_name)
        assert husband_share.fraction == 1/4
    
    def test_husband_without_descendants(self, calculator):
        """Test husband gets 1/2 when no descendants."""
        heirs = Heirs(husband=True)
        result = calculator.calculate(100000, heirs)
        
        husband_share = next(s for s in result.distribution if "Husband" in s.heir_name)
        assert husband_share.fraction == 1/2
    
    def test_wife_with_descendants(self, calculator):
        """Test wife gets 1/8 when there are descendants."""
        heirs = Heirs(wife_count=1, sons=1)
        result = calculator.calculate(100000, heirs)
        
        wife_share = next(s for s in result.distribution if "Wife" in s.heir_name)
        assert wife_share.fraction == 1/8
    
    def test_wife_without_descendants(self, calculator):
        """Test wife gets 1/4 when no descendants."""
        heirs = Heirs(wife_count=1)
        result = calculator.calculate(100000, heirs)
        
        wife_share = next(s for s in result.distribution if "Wife" in s.heir_name)
        assert wife_share.fraction == 1/4
    
    def test_multiple_wives(self, calculator):
        """Test multiple wives share 1/4 (without descendants)."""
        heirs = Heirs(wife_count=2)
        result = calculator.calculate(100000, heirs)
        
        wife_share = next(s for s in result.distribution if "Wife" in s.heir_name)
        assert wife_share.fraction == 1/4  # Total share, split between 2
    
    def test_mother_without_siblings(self, calculator):
        """Test mother gets 1/3 when no siblings of deceased."""
        heirs = Heirs(mother=True, father=True)
        result = calculator.calculate(100000, heirs)
        
        mother_share = next(s for s in result.distribution if "Mother" in s.heir_name)
        assert mother_share.fraction == 1/3
    
    def test_mother_with_siblings(self, calculator):
        """Test mother gets 1/6 when there are siblings."""
        heirs = Heirs(mother=True, full_brothers=2)
        result = calculator.calculate(100000, heirs)
        
        mother_share = next(s for s in result.distribution if "Mother" in s.heir_name)
        assert mother_share.fraction == 1/6
    
    def test_father_with_sons(self, calculator):
        """Test father gets 1/6 + asabah when there are sons."""
        heirs = Heirs(father=True, sons=1)
        result = calculator.calculate(100000, heirs)
        
        father_share = next(s for s in result.distribution if "Father" in s.heir_name)
        # Should have fard + asabah basis
        assert "fard" in father_share.basis
    
    def test_daughter_single(self, calculator):
        """Test single daughter gets 1/2 when no sons."""
        heirs = Heirs(daughters=1)
        result = calculator.calculate(100000, heirs)
        
        daughter_share = next(s for s in result.distribution if "Daughter" in s.heir_name)
        assert daughter_share.fraction == 1/2
    
    def test_daughters_multiple(self, calculator):
        """Test 2+ daughters share 2/3 when no sons."""
        heirs = Heirs(daughters=2)
        result = calculator.calculate(100000, heirs)
        
        daughter_share = next(s for s in result.distribution if "Daughter" in s.heir_name)
        assert daughter_share.fraction == 2/3
    
    # ==========================================
    # Complete Scenario Tests
    # ==========================================
    
    def test_simple_case_husband_parents_children(self, calculator):
        """Test common case: husband, parents, son, daughter."""
        heirs = Heirs(husband=True, father=True, mother=True, sons=1, daughters=1)
        result = calculator.calculate(100000, heirs)
        
        # Verify total equals estate (within rounding)
        total = sum(s.amount for s in result.distribution)
        assert abs(total - 100000) < 1  # Within $1
    
    def test_wife_parents_only(self, calculator):
        """Test: wife, father, mother (no descendants)."""
        heirs = Heirs(wife_count=1, father=True, mother=True)
        result = calculator.calculate(100000, heirs)
        
        # Wife: 1/4, Mother: 1/3 of remainder, Father: asabah
        wife_share = next(s for s in result.distribution if "Wife" in s.heir_name)
        assert wife_share.fraction == 1/4
    
    def test_daughters_only_with_radd(self, calculator):
        """Test: daughters only, remainder redistributed (radd)."""
        heirs = Heirs(daughters=2)
        result = calculator.calculate(100000, heirs)
        
        # 2 daughters get 2/3, remainder returned via radd
        assert result.method == "radd"
        total = sum(s.amount for s in result.distribution)
        assert abs(total - 100000) < 1
    
    # ==========================================
    # 'Awl Tests
    # ==========================================
    
    def test_awl_case(self, calculator):
        """Test 'awl: sum of shares exceeds 1."""
        # Classic 'awl case: husband + 2 sisters + mother
        # 1/2 + 2/3 + 1/3 = 13/6 > 1
        heirs = Heirs(husband=True, full_sisters=2, mother=True)
        result = calculator.calculate(100000, heirs)
        
        assert result.method == "awl"
        # Total should still equal estate (reduced proportionally)
        total = sum(s.amount for s in result.distribution)
        assert abs(total - 100000) < 1
    
    # ==========================================
    # Radd Tests
    # ==========================================
    
    def test_radd_no_asabah(self, calculator):
        """Test radd when no residuary heirs."""
        # Mother only gets 1/3, no asabah → radd
        heirs = Heirs(mother=True)
        result = calculator.calculate(100000, heirs)
        
        assert result.method == "radd"
        total = sum(s.amount for s in result.distribution)
        assert abs(total - 100000) < 1
    
    # ==========================================
    # Blocked Heirs Tests
    # ==========================================
    
    def test_son_blocks_grandson(self, calculator):
        """Test son blocks grandson from inheritance."""
        heirs_with_grandson = Heirs(sons=1, grandsons=1, father=True)
        result = calculator.calculate(100000, heirs_with_grandson)
        
        # Grandson should not appear in distribution
        assert not any("Grandson" in s.heir_name for s in result.distribution)
    
    def test_father_blocks_grandfather(self, calculator):
        """Test father blocks paternal grandfather."""
        heirs = Heirs(father=True, paternal_grandfather=True, mother=True)
        result = calculator.calculate(100000, heirs)
        
        # Grandfather should not appear
        assert not any("Grandfather" in s.heir_name for s in result.distribution)
    
    # ==========================================
    # Madhhab Tests
    # ==========================================
    
    def test_madhhab_note_present(self, calculator):
        """Test madhhab-specific notes appear for disputed cases."""
        # Grandfather + brothers = disputed case
        heirs = Heirs(paternal_grandfather=True, full_brothers=2)
        result = calculator.calculate(100000, heirs, madhhab="shafii")
        
        assert result.school_opinion is not None
    
    # ==========================================
    # Edge Cases
    # ==========================================
    
    def test_zero_estate_error(self, calculator):
        """Test error on zero or negative estate."""
        heirs = Heirs(husband=True)
        
        with pytest.raises(ValueError):
            calculator.calculate(0, heirs)
        
        with pytest.raises(ValueError):
            calculator.calculate(-1000, heirs)
    
    def test_debts_deduction(self, calculator):
        """Test debts are deducted before distribution."""
        heirs = Heirs(husband=True, sons=1)
        result = calculator.calculate(100000, heirs, debts=20000)
        
        # Net estate should be 80000
        assert result.estate_value == 80000
    
    def test_wasiyyah_max_one_third(self, calculator):
        """Test bequests limited to max 1/3."""
        heirs = Heirs(husband=True)
        result = calculator.calculate(100000, heirs, wasiyyah=50000)
        
        # Wasiyyah should be capped at 1/3 of remaining
        assert result.estate_value >= 66666  # At least 2/3 remains
    
    def test_no_heirs(self, calculator):
        """Test behavior with no heirs defined."""
        heirs = Heirs()
        result = calculator.calculate(100000, heirs)
        
        # Should handle gracefully
        assert result is not None
    
    # ==========================================
    # Accuracy Tests
    # ==========================================
    
    def test_distribution_accuracy(self, calculator):
        """Test that distribution totals match estate value."""
        test_cases = [
            Heirs(husband=True, father=True, mother=True, sons=1),
            Heirs(wife_count=1, daughters=2),
            Heirs(mother=True, full_sisters=2),
            Heirs(husband=True, mother=True),
        ]
        
        estate = 100000
        for heirs in test_cases:
            result = calculator.calculate(estate, heirs)
            total = sum(s.amount for s in result.distribution)
            
            assert abs(total - estate) < 1, f"Total {total} != {estate} for {heirs}"
    
    def test_references_present(self, calculator):
        """Test references are included in result."""
        heirs = Heirs(husband=True, sons=1)
        result = calculator.calculate(100000, heirs)
        
        assert len(result.references) > 0
        assert any("Quran" in ref for ref in result.references)
    
    def test_notes_present(self, calculator):
        """Test explanatory notes are included."""
        heirs = Heirs(husband=True, sons=1)
        result = calculator.calculate(100000, heirs)
        
        assert len(result.notes) > 0
