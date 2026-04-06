#!/usr/bin/env python3
"""
Test CAMeL Tools integration for Athar Islamic QA System.

Demonstrates how CAMeL Tools improves Arabic text processing.
Usage:
    python scripts/test_camel_tools.py
"""

def test_dediac():
    """Test diacritic removal."""
    try:
        from camel_tools.utils.dediac import dediac_ar
        
        # Test cases from Quran
        test_cases = [
            "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ",
            "ٱللَّهُ لَآ إِلَـٰهَ إِلَّا هُوَ",
            "ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَـٰلَمِينَ",
        ]
        
        print("✅ CAMeL Tools - Diacritic Removal Test")
        print("="*60)
        
        for text in test_cases:
            dediac = dediac_ar(text)
            print(f"\nOriginal: {text}")
            print(f"Normalized: {dediac}")
        
        return True
        
    except ImportError:
        print("❌ CAMeL Tools not installed")
        print("\nInstall with: pip install camel-tools")
        return False

def test_tokenization():
    """Test Arabic tokenization."""
    try:
        from camel_tools.tokenizers.word import word_tokenize
        
        text = "بسم الله الرحمن الرحيم"
        tokens = word_tokenize(text)
        
        print("\n✅ CAMeL Tools - Tokenization Test")
        print("="*60)
        print(f"\nText: {text}")
        print(f"Tokens: {tokens}")
        
        return True
        
    except ImportError:
        return False

def test_morphological():
    """Test morphological analysis."""
    try:
        from camel_tools.disambig.mle import MLEDisambiguator
        
        print("\n✅ CAMeL Tools - Morphological Analysis Test")
        print("="*60)
        
        # Load pretrained disambiguator
        mle = MLEDisambiguator.pretrained()
        
        # Test word
        word = "يكتبون"
        disambig = mle.disambiguate(word)
        
        print(f"\nWord: {word}")
        print(f"Analyses: {len(disambig)}")
        for i, analysis in enumerate(disambig[:3], 1):
            print(f"  {i}. {analysis.analysis}")
        
        return True
        
    except ImportError:
        return False

def main():
    """Run all tests."""
    print("\n🐫 CAMeL Tools Integration Test for Athar")
    print("="*60)
    
    results = []
    
    # Test 1: Diacritic removal
    results.append(("Diacritic Removal", test_dediac()))
    
    # Test 2: Tokenization
    results.append(("Tokenization", test_tokenization()))
    
    # Test 3: Morphological
    results.append(("Morphological Analysis", test_morphological()))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 CAMeL Tools is ready for Athar integration!")
    else:
        print("\n⚠️ Install CAMeL Tools: pip install camel-tools")

if __name__ == "__main__":
    main()
