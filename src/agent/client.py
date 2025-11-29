"""Claude Agent SDK client wrapper."""

import logging
from typing import Optional

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, TextBlock, ResultMessage

from .config import get_settings

logger = logging.getLogger(__name__)


class AgentClient:
    """Wrapper around Claude Agent SDK using ClaudeSDKClient for session management."""

    def __init__(
        self,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_turns: Optional[int] = None,
        cwd: Optional[str] = None,
        allowed_tools: Optional[list[str]] = None,
    ):
        """Initialize agent client.

        Args:
            system_prompt: Custom system prompt (uses default if not provided)
            model: Model to use (uses settings default if not provided)
            max_turns: Maximum conversation turns
            cwd: Working directory for file operations
            allowed_tools: List of permitted tools
        """
        self._settings = get_settings()
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.model = model or self._settings.model
        self.max_turns = max_turns or 20
        self.cwd = cwd or "/tmp"
        self.allowed_tools = allowed_tools or ["Read", "Glob", "Grep"]

    def _default_system_prompt(self) -> str:
        """Default system prompt for the agent."""
        return """You are a helpful AI assistant powered by Claude.

You can help with:
- Answering questions
- Analyzing information
- Writing and reviewing content
- Problem-solving

Be concise, accurate, and helpful in your responses."""

    def _get_options(self) -> ClaudeAgentOptions:
        """Build SDK options."""
        return ClaudeAgentOptions(
            system_prompt=self.system_prompt,
            model=self.model,
            max_turns=self.max_turns,
            cwd=self.cwd,
            allowed_tools=self.allowed_tools,
            permission_mode="acceptEdits",
        )

    async def query(self, prompt: str) -> str:
        """Execute a query and return the response using ClaudeSDKClient.

        Args:
            prompt: The user's query

        Returns:
            The agent's response as a string
        """
        self._settings.validate_api_key()
        logger.info(f"Processing query: {prompt[:100]}...")

        options = self._get_options()
        response_text = ""

        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)

            async for message in client.receive_response():
                logger.debug(f"Received message type: {type(message).__name__}")

                # Handle AssistantMessage with TextBlocks
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            response_text = block.text

                # Handle ResultMessage (final message with result)
                elif isinstance(message, ResultMessage):
                    if hasattr(message, 'result') and message.result:
                        response_text = message.result

        return response_text or "No response generated."
