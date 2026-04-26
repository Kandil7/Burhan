"""
Era Classifier for Burhan Islamic QA system.

Classifies Islamic scholars into historical eras based on death year (Hijri).
Extracted from duplicate code in HybridSearcher, CitationNormalizer, and HadithGrader.

Eras:
- Prophetic: 0-100 AH (Companions)
- Tabi'un: 100-200 AH (Successors)
- Classical: 200-500 AH (Golden age)
- Medieval: 500-900 AH (Post-classical)
- Ottoman: 900-1300 AH (Ottoman era)
- Modern: 1300+ AH (Modern era)

Usage:
    era = EraClassifier.classify(179)  # "classical" - Imam Malik
"""
from enum import Enum


class Era(str, Enum):
    """Islamic scholarly eras."""
    PROPHETIC = "prophetic"        # 0-100 AH - Companions
    TABIUN = "tabiun"              # 100-200 AH - Successors
    CLASSICAL = "classical"        # 200-500 AH - Golden age
    MEDIEVAL = "medieval"          # 500-900 AH - Post-classical
    OTTOMAN = "ottoman"            # 900-1300 AH - Ottoman era
    MODERN = "modern"              # 1300+ AH - Modern era


class EraClassifier:
    """
    Classifies scholars into eras based on death year.

    Usage:
        era = EraClassifier.classify(179)  # "classical"
    """

    # Era boundaries in Hijri years
    PROPHETIC_END = 100
    TABIUN_END = 200
    CLASSICAL_END = 500
    MEDIEVAL_END = 900
    OTTOMAN_END = 1300

    @staticmethod
    def classify(death_year_hijri: int) -> str:
        """
        Classify scholar's era based on death year (Hijri).

        Args:
            death_year_hijri: Death year in Hijri calendar

        Returns:
            Era classification string

        Examples:
            >>> EraClassifier.classify(50)    # Prophetic - Abu Bakr
            'prophetic'
            >>> EraClassifier.classify(150)   # Tabiun
            'tabiun'
            >>> EraClassifier.classify(179)   # Classical - Imam Malik
            'classical'
            >>> EraClassifier.classify(600)   # Medieval - Al-Nawawi
            'medieval'
            >>> EraClassifier.classify(1000)  # Ottoman - Ibn Hajar
            'ottoman'
            >>> EraClassifier.classify(1400)  # Modern
            'modern'
        """
        if death_year_hijri <= EraClassifier.PROPHETIC_END:
            return Era.PROPHETIC.value
        elif death_year_hijri <= EraClassifier.TABIUN_END:
            return Era.TABIUN.value
        elif death_year_hijri <= EraClassifier.CLASSICAL_END:
            return Era.CLASSICAL.value
        elif death_year_hijri <= EraClassifier.MEDIEVAL_END:
            return Era.MEDIEVAL.value
        elif death_year_hijri <= EraClassifier.OTTOMAN_END:
            return Era.OTTOMAN.value
        else:
            return Era.MODERN.value

    @staticmethod
    def get_era_description(era: str) -> str:
        """
        Get human-readable description of an era.

        Args:
            era: Era string from classify()

        Returns:
            Description of the era
        """
        descriptions = {
            Era.PROPHETIC.value: "Prophetic Era (Companions of the Prophet)",
            Era.TABIUN.value: "Tabi'un Era (Successors)",
            Era.CLASSICAL.value: "Classical Islamic Golden Age",
            Era.MEDIEVAL.value: "Medieval/Post-Classical Period",
            Era.OTTOMAN.value: "Ottoman Era",
            Era.MODERN.value: "Modern Era",
        }
        return descriptions.get(era, "Unknown Era")
