"""Claude API client wrapper using the Anthropic SDK."""

import logging
from typing import Optional

from anthropic import AsyncAnthropic

from .config import get_settings

logger = logging.getLogger(__name__)


class AgentClient:
    """Wrapper around Anthropic API with sensible defaults."""

    def __init__(
        self,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
    ):
        """Initialize agent client.

        Args:
            system_prompt: Custom system prompt (uses default if not provided)
            model: Model to use (uses settings default if not provided)
            max_tokens: Maximum tokens in response
        """
        self._settings = get_settings()
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.model = model or self._settings.model
        self.max_tokens = max_tokens
        self._client: Optional[AsyncAnthropic] = None

    def _default_system_prompt(self) -> str:
        """Default system prompt for the agent."""
        return """You are a helpful AI assistant powered by Claude.

You can help with:
- Answering questions
- Analyzing information
- Writing and reviewing content
- Problem-solving

Be concise, accurate, and helpful in your responses."""

    def _get_client(self) -> AsyncAnthropic:
        """Get or create Anthropic client."""
        if self._client is None:
            self._settings.validate_api_key()
            self._client = AsyncAnthropic(api_key=self._settings.anthropic_api_key)
        return self._client

    async def query(self, prompt: str) -> str:
        """Execute a query and return the response.

        Args:
            prompt: The user's query

        Returns:
            The agent's response as a string
        """
        logger.info(f"Processing query: {prompt[:100]}...")

        client = self._get_client()

        message = await client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=self.system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract text from response
        if message.content and len(message.content) > 0:
            return message.content[0].text

        return "No response generated."
