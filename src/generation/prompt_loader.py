"""
Prompt Loader for Generation Layer.

Loads prompts from files for answer generation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.generation.schemas import PromptTemplate


class PromptLoader:
    """
    Loads prompts from files.

    Usage:
        loader = PromptLoader()
        prompt = loader.load("fiqh")
    """

    def __init__(self, prompts_dir: Path | None = None):
        """
        Initialize prompt loader.

        Args:
            prompts_dir: Path to prompts directory
        """
        from src.config.loader import PROMPTS_DIR

        self._prompts_dir = prompts_dir or PROMPTS_DIR
        self._loaded_prompts: dict[str, PromptTemplate] = {}

    def load(self, agent_name: str) -> PromptTemplate:
        """
        Load prompt for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            PromptTemplate instance
        """
        if agent_name in self._loaded_prompts:
            return self._loaded_prompts[agent_name]

        # Load shared preamble
        preamble = ""
        preamble_path = self._prompts_dir / "_shared_preamble.txt"
        if preamble_path.exists():
            with open(preamble_path, "r", encoding="utf-8") as f:
                preamble = f.read().strip()

        # Load agent prompt
        agent_prompt_path = self._prompts_dir / f"{agent_name}_agent.txt"
        if not agent_prompt_path.exists():
            raise FileNotFoundError(f"Prompt not found: {agent_prompt_path}")

        with open(agent_prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read().strip()

        # Combine preamble and agent prompt
        if preamble:
            system_prompt = f"{preamble}\n\n{system_prompt}"

        # Build template
        template = PromptTemplate(
            name=agent_name,
            system_prompt=system_prompt,
            user_template="{query}\n\nالنصوص:\n{passages}",
            required_variables=["query", "passages"],
        )

        self._loaded_prompts[agent_name] = template
        return template

    def format_user_prompt(
        self,
        agent_name: str,
        query: str,
        passages: str,
        language: str = "ar",
    ) -> str:
        """
        Format user prompt with variables.

        Args:
            agent_name: Agent name
            query: User query
            passages: Formatted passages
            language: Output language

        Returns:
            Formatted prompt string
        """
        template = self.load(agent_name)

        return template.user_template.format(
            query=query,
            passages=passages,
            language=language,
        )


# Singleton instance
_prompt_loader: PromptLoader | None = None


def get_prompt_loader() -> PromptLoader:
    """Get the global prompt loader instance."""
    global _prompt_loader
    if _prompt_loader is None:
        _prompt_loader = PromptLoader()
    return _prompt_loader


__all__ = ["PromptLoader", "get_prompt_loader"]
