"""Claude Agent SDK client wrapper."""

import logging
from typing import AsyncIterator, Optional

from claude_code_sdk import query as sdk_query, ClaudeCodeOptions

from .config import get_settings

logger = logging.getLogger(__name__)


class AgentClient:
    """Wrapper around Claude Agent SDK with sensible defaults."""

    def __init__(
        self,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_turns: Optional[int] = None,
        cwd: Optional[str] = None,
    ):
        """Initialize agent client.

        Args:
            system_prompt: Custom system prompt (uses default if not provided)
            model: Model to use (uses settings default if not provided)
            max_turns: Maximum conversation turns (uses settings default if not provided)
            cwd: Working directory for file operations
        """
        self._settings = get_settings()
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.model = model or self._settings.model
        self.max_turns = max_turns or self._settings.max_turns
        self.cwd = cwd

    def _default_system_prompt(self) -> str:
        """Default system prompt for the agent."""
        return """You are a helpful AI assistant powered by Claude.

You can help with:
- Answering questions
- Analyzing information
- Writing and reviewing content
- Problem-solving

Be concise, accurate, and helpful in your responses."""

    def _get_options(self) -> ClaudeCodeOptions:
        """Build SDK options from settings."""
        return ClaudeCodeOptions(
            system_prompt=self.system_prompt,
            model=self.model,
            max_turns=self.max_turns,
            allowed_tools=self._settings.allowed_tools,
            disallowed_tools=self._settings.disallowed_tools,
            cwd=self.cwd,
        )

    async def query(self, prompt: str) -> str:
        """Execute a one-off query and return the final response.

        Args:
            prompt: The user's query

        Returns:
            The agent's response as a string
        """
        # Validate API key before making request
        self._settings.validate_api_key()

        logger.info(f"Processing query: {prompt[:100]}...")

        options = self._get_options()
        messages = []

        async for message in sdk_query(prompt=prompt, options=options):
            messages.append(message)
            logger.debug(f"Received message type: {type(message).__name__}")

        # Extract final text response
        if messages:
            last_message = messages[-1]
            # Handle different message types from SDK
            # ResultMessage has 'result' attribute with the final answer
            if hasattr(last_message, 'result'):
                return str(last_message.result)
            # AssistantMessage has 'content' attribute
            if hasattr(last_message, 'content'):
                return str(last_message.content)
            return str(last_message)

        return "No response generated."

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        """Stream responses from the agent.

        Args:
            prompt: The user's query

        Yields:
            Response chunks as they arrive
        """
        logger.info(f"Streaming query: {prompt[:100]}...")

        options = self._get_options()

        async for message in sdk_query(prompt=prompt, options=options):
            if hasattr(message, 'content'):
                yield str(message.content)
            else:
                yield str(message)
