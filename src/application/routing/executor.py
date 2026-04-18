"""
Executor for Agent Execution.

Executes queries against agents based on plans.
"""

from __future__ import annotations

from typing import Any

from src.agents.base import AgentOutput


class ExecutionResult:
    """Result of agent execution."""

    def __init__(
        self,
        agent_name: str,
        success: bool,
        output: AgentOutput | None = None,
        error: str | None = None,
        timing_ms: float | None = None,
    ):
        self.agent_name = agent_name
        self.success = success
        self.output = output
        self.error = error
        self.timing_ms = timing_ms


class AgentExecutor:
    """
    Executes queries against agents.

    Handles:
    - Single agent execution
    - Sequential execution
    - Parallel execution

    Usage:
        executor = AgentExecutor()
        result = await executor.execute("fiqh", query)
    """

    def __init__(self):
        """Initialize the executor."""
        self._agent_registry = {}

    def register_agent(self, name: str, agent: Any):
        """Register an agent for execution."""
        self._agent_registry[name] = agent

    async def execute(
        self,
        agent_name: str,
        query: str,
        language: str = "ar",
        **kwargs,
    ) -> ExecutionResult:
        """
        Execute query against a single agent.

        Args:
            agent_name: Name of the agent
            query: User query
            language: Query language
            **kwargs: Additional parameters

        Returns:
            ExecutionResult
        """
        import time

        start_time = time.time()

        agent = self._agent_registry.get(agent_name)

        if not agent:
            return ExecutionResult(
                agent_name=agent_name,
                success=False,
                error=f"Agent {agent_name} not found",
            )

        try:
            from src.agents.base import AgentInput

            output = await agent.execute(AgentInput(query=query, language=language, metadata=kwargs))

            timing_ms = (time.time() - start_time) * 1000

            return ExecutionResult(
                agent_name=agent_name,
                success=True,
                output=output,
                timing_ms=timing_ms,
            )
        except Exception as e:
            timing_ms = (time.time() - start_time) * 1000
            return ExecutionResult(
                agent_name=agent_name,
                success=False,
                error=str(e),
                timing_ms=timing_ms,
            )

    async def execute_sequential(
        self,
        agent_names: list[str],
        query: str,
        language: str = "ar",
    ) -> list[ExecutionResult]:
        """Execute agents sequentially."""
        results = []

        for agent_name in agent_names:
            result = await self.execute(agent_name, query, language)
            results.append(result)

            # Stop on first failure if critical
            if not result.success:
                break

        return results

    async def execute_parallel(
        self,
        agent_names: list[str],
        query: str,
        language: str = "ar",
    ) -> list[ExecutionResult]:
        """Execute agents in parallel."""
        import asyncio

        tasks = [self.execute(agent_name, query, language) for agent_name in agent_names]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to failed results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    ExecutionResult(
                        agent_name=agent_names[i],
                        success=False,
                        error=str(result),
                    )
                )
            else:
                processed_results.append(result)

        return processed_results


__all__ = ["ExecutionResult", "AgentExecutor"]
