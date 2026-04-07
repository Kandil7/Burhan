#!/usr/bin/env python3
"""
Complete Athar Islamic QA System - Working Query Handler

Bypasses orchestrator issues by directly using components.
"""
import asyncio
from src.agents.chatbot_agent import ChatbotAgent
from src.agents.base import AgentInput
from src.config.intents import Intent
from src.core.router import HybridQueryClassifier
from src.infrastructure.llm_client import get_llm_client

async def test_full_pipeline():
    """Test the full query pipeline."""
    print("=== Athar Full Pipeline Test ===\n")
    
    # Initialize LLM
    llm_client = await get_llm_client()
    print(f"✓ LLM Client: {type(llm_client).__name__}")
    
    # Initialize classifier
    classifier = HybridQueryClassifier(llm_client=llm_client)
    print(f"✓ Classifier: Ready")
    
    # Initialize chatbot
    chatbot = ChatbotAgent()
    print(f"✓ Chatbot: {chatbot.name}")
    
    # Test queries
    test_queries = [
        ("السلام عليكم", "Greeting"),
        ("ما حكم الصلاة؟", "Fiqh"),
        ("كم عدد آيات الفاتحة؟", "Quran"),
        ("أعطني دعاء السفر", "Dua"),
    ]
    
    print("\n--- Testing Queries ---\n")
    for query, desc in test_queries:
        print(f"Query: {query} ({desc})")
        result = await classifier.classify(query)
        print(f"  Intent: {result.intent.value} (confidence: {result.confidence:.2f})")
        
        # Use chatbot for response
        agent_result = await chatbot.execute(AgentInput(query=query, language="ar", metadata={}))
        print(f"  Answer: {agent_result.answer[:60]}...\n")
    
    print("=== Test Complete ===")

asyncio.run(test_full_pipeline())
