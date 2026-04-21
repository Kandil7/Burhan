import asyncio
from src.verification.checks.exact_quote import exact_quote_verifier

async def main():
    claim = "كما قال تعالى: ﴿لَتَجِدَنَّ أَشَدَّ النَّاسِ عَدَاوَةً لِّلَّذِينَ آمَنُوا اليَهُودَ﴾ وفي السيرة قال الرسول «السلام عليكم»"
    evidence = [
        {"text": "الرسول قال السلام عليكم ورحمة الله"},
        {"text": "وقد حذرنا الله من اليهود"}
    ]
    
    result = await exact_quote_verifier.verify(claim, evidence)
    print("Passed:", result.passed)
    print("Message:", result.message)
    print("Details:", result.details)

asyncio.run(main())
