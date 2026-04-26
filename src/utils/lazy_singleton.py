"""
Lazy Singleton Pattern for Burhan Islamic QA system.

Thread-safe lazy initialization singleton to eliminate boilerplate code.
Replaces the repeated global+lock+getter pattern across the codebase.

Usage:
    _chatbot = LazySingleton(ChatbotAgent)
    chatbot = _chatbot.get()

    _classifier = LazySingleton(lambda: HybridQueryClassifier(llm_client=...))
    classifier = await _classifier.get_async()  # For async factories
"""
import asyncio
import threading
from collections.abc import Callable
from typing import Generic, TypeVar

T = TypeVar("T")


class LazySingleton(Generic[T]):
    """
    Thread-safe lazy singleton for synchronous factories.

    Eliminates the need for:
        _instance = None
        _lock = threading.Lock()

        def get_instance():
            global _instance
            with _lock:
                if _instance is None:
                    _instance = Factory()
                return _instance

    Usage:
        _chatbot = LazySingleton(ChatbotAgent)
        chatbot = _chatbot.get()

        # For testing
        _chatbot.reset()
    """

    def __init__(self, factory: Callable[[], T]):
        """
        Initialize lazy singleton.

        Args:
            factory: Callable that creates the instance (no arguments)
        """
        self._factory = factory
        self._lock = threading.Lock()
        self._instance: T | None = None

    def get(self) -> T:
        """
        Get or create the singleton instance.

        Returns:
            The singleton instance
        """
        if self._instance is None:
            with self._lock:
                # Double-checked locking
                if self._instance is None:
                    self._instance = self._factory()
        return self._instance

    def reset(self) -> None:
        """Reset the instance (useful for testing)."""
        with self._lock:
            self._instance = None

    @property
    def is_initialized(self) -> bool:
        """Check if instance has been created."""
        return self._instance is not None


class AsyncLazySingleton(Generic[T]):
    """
    Async-safe lazy singleton for async factories.

    Usage:
        _classifier = AsyncLazySingleton(
            lambda: HybridQueryClassifier(llm_client=...)
        )
        classifier = await _classifier.get()
    """

    def __init__(self, factory: Callable[[], T]):
        """
        Initialize async lazy singleton.

        Args:
            factory: Async callable that creates the instance
        """
        self._factory = factory
        self._lock = asyncio.Lock()
        self._instance: T | None = None

    async def get(self) -> T:
        """
        Get or create the singleton instance.

        Returns:
            The singleton instance
        """
        if self._instance is None:
            async with self._lock:
                # Double-checked locking
                if self._instance is None:
                    if asyncio.iscoroutinefunction(self._factory):
                        self._instance = await self._factory()
                    else:
                        self._instance = self._factory()
        return self._instance

    async def reset(self) -> None:
        """Reset the instance (useful for testing)."""
        async with self._lock:
            self._instance = None

    @property
    def is_initialized(self) -> bool:
        """Check if instance has been created."""
        return self._instance is not None
