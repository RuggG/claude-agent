"""Configuration management for Claude Agent SDK."""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Settings:
    """Application settings loaded from environment."""

    # API Configuration
    anthropic_api_key: str = field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", ""))

    # Model Configuration
    model: str = field(default_factory=lambda: os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-5-20250929"))
    max_turns: int = field(default_factory=lambda: int(os.environ.get("MAX_TURNS", "20")))

    # Server Configuration
    port: int = field(default_factory=lambda: int(os.environ.get("PORT", "8080")))
    host: str = field(default_factory=lambda: os.environ.get("HOST", "0.0.0.0"))

    # Tool Configuration
    allowed_tools: list[str] = field(default_factory=lambda: [
        "Read", "Write", "Edit", "Glob", "Grep"
    ])
    disallowed_tools: list[str] = field(default_factory=lambda: [
        "Bash"  # Restrict shell access by default for safety
    ])

    def validate_api_key(self):
        """Validate API key is present. Call before making API requests."""
        if not self.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. "
                "Set it in environment or add to keychain: "
                "security add-generic-password -U -a \"$USER\" -s ANTHROPIC_API_KEY -w 'sk-ant-...'"
            )

    @classmethod
    def load(cls) -> "Settings":
        """Load settings from environment."""
        return cls()


# Singleton instance - lazy loaded
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings.load()
    return _settings


# For convenience
settings = property(get_settings)
