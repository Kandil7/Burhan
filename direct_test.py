"""Test integration layer by writing output to file."""

import asyncio
import sys
import os

# Ensure proper encoding
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

output_lines = []


async def test():
    try:
        output_lines.append("Starting test...")

        # Step 1: Create classifier and router
        output_lines.append("Creating classifier...")
        from src.application.router import RouterAgent
        from src.application.hybrid_classifier import HybridIntentClassifier

        classifier = HybridIntentClassifier()
        router = RouterAgent(classifier=classifier)

        # Step 2: Classify
        output_lines.append("Classifying query...")
        decision = await router.route("test")
        output_lines.append(f"Intent: {decision.result.intent.value}")

        # Step 3: Get agent
        output_lines.append("Getting agent from registry...")
        from src.core.registry import get_registry

        registry = get_registry()
        agent, is_agent = registry.get_for_intent(decision.result.intent)
        output_lines.append(f"Agent: {type(agent).__name__ if agent else None}")

        # Step 4: Execute
        if agent:
            output_lines.append("Executing agent...")
            from src.agents.base import AgentInput

            agent_input = AgentInput(query="test", language="ar", metadata={})
            result = await agent.execute(agent_input)
            output_lines.append(f"Answer: {result.answer[:50]}")
        else:
            output_lines.append("NO AGENT FOUND!")

        output_lines.append("DONE!")
    except Exception as e:
        import traceback

        output_lines.append(f"ERROR: {type(e).__name__}: {e}")
        output_lines.append(traceback.format_exc())


asyncio.run(test())

# Write output
with open("test_output.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))
print("Test complete - output written to test_output.txt")
