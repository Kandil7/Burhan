"""
Language Detection Utility for Athar Islamic QA system.

Detects if text is Arabic or English based on Unicode character analysis.
Extracted from duplicate code in HybridQueryClassifier and ChatbotAgent.

Usage:
    lang = detect_language("ما حكم صلاة العيد؟")  # "ar"
    lang = detect_language("How to calculate zakat?")  # "en"
"""


def detect_language(text: str, threshold: float = 0.3) -> str:
    """
    Detect if text is Arabic or English.
    
    Uses Unicode range detection for Arabic script.
    Arabic Unicode range: U+0600 to U+06FF
    Arabic Extended-A: U+0750 to U+077F
    
    Args:
        text: Input text
        threshold: Minimum ratio of Arabic chars to be considered Arabic (default: 0.3)
        
    Returns:
        "ar" if Arabic, "en" otherwise
        
    Examples:
        >>> detect_language("ما حكم صلاة العيد؟")
        "ar"
        >>> detect_language("How to calculate zakat?")
        "en"
        >>> detect_language("مرحبا hello")  # Mixed, >30% Arabic
        "ar"
        >>> detect_language("hello мир")  # Russian, <30% Arabic
        "en"
    """
    if not text or not text.strip():
        return "ar"  # Default to Arabic for empty text
    
    # Count Arabic characters
    arabic_chars = sum(
        1 for char in text
        if '\u0600' <= char <= '\u06FF'  # Basic Arabic
        or '\u0750' <= char <= '\u077F'  # Arabic Extended-A
    )
    
    # Total non-whitespace characters
    total_chars = len(text.replace(" ", "").replace("\t", "").replace("\n", ""))
    
    if total_chars == 0:
        return "ar"
    
    # Calculate ratio
    arabic_ratio = arabic_chars / total_chars
    
    return "ar" if arabic_ratio > threshold else "en"


def is_mostly_arabic(text: str, threshold: float = 0.5) -> bool:
    """
    Check if text is mostly Arabic (>50% by default).
    
    Args:
        text: Input text
        threshold: Minimum ratio (default: 0.5)
        
    Returns:
        True if mostly Arabic
    """
    return detect_language(text, threshold=threshold) == "ar"


def is_mostly_english(text: str, threshold: float = 0.5) -> bool:
    """
    Check if text is mostly English.
    
    Args:
        text: Input text
        threshold: Minimum ratio for Arabic (if below, considered English)
        
    Returns:
        True if mostly English
    """
    return detect_language(text, threshold=threshold) == "en"
