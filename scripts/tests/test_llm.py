import asyncio
from src.infrastructure.llm_client import get_llm_client
from src.config.settings import settings

async def test():
    print(f"Provider: {settings.llm_provider}")
    print(f"Groq key set: {bool(settings.groq_api_key)}")
    print(f"HF token set: {bool(settings.hf_token)}")
    
    client = await get_llm_client()
    print(f'Client type: {type(client).__name__}')
    
    try:
        resp = await client.chat.completions.create(
            model='qwen/qwen3-32b' if settings.llm_provider == 'groq' else settings.openai_model,
            messages=[{'role':'user','content':'ما هو الإسلام؟'}],
            temperature=0.1,
            max_tokens=100
        )
        print(f'Response: {resp.choices[0].message.content[:150]}')
    except Exception as e:
        print(f'LLM Error: {e}')

asyncio.run(test())
