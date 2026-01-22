"""Settings management for AlgoAtlas."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class LeetCodeSettings:
    """LeetCode scraper settings."""

    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 2


@dataclass
class VerifierSettings:
    """Solution verifier settings."""

    execution_timeout: int = 5


@dataclass
class ClaudeSettings:
    """Claude Code settings."""

    model: Optional[str] = None


@dataclass
class Settings:
    """Application settings."""

    vault_path: Optional[str] = None
    leetcode: LeetCodeSettings = field(default_factory=LeetCodeSettings)
    verifier: VerifierSettings = field(default_factory=VerifierSettings)
    claude: ClaudeSettings = field(default_factory=ClaudeSettings)

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Settings":
        """Load settings from YAML config file.

        Args:
            config_path: Path to config file. If None, searches default locations.

        Returns:
            Settings instance with loaded or default values.
        """
        settings = cls()

        if config_path is None:
            config_path = cls._find_config_file()

        if config_path and Path(config_path).exists():
            settings = cls._load_from_file(config_path)

        return settings

    @classmethod
    def _find_config_file(cls) -> Optional[str]:
        """Search for config file in default locations."""
        search_paths = [
            Path.cwd() / "config" / "config.yaml",
            Path.cwd() / "config.yaml",
            Path.home() / ".config" / "algo-atlas" / "config.yaml",
            Path.home() / ".algo-atlas" / "config.yaml",
        ]

        for path in search_paths:
            if path.exists():
                return str(path)

        return None

    @classmethod
    def _load_from_file(cls, config_path: str) -> "Settings":
        """Load settings from a YAML file."""
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        leetcode_data = data.get("leetcode", {})
        verifier_data = data.get("verifier", {})
        claude_data = data.get("claude", {})

        return cls(
            vault_path=data.get("vault_path"),
            leetcode=LeetCodeSettings(
                timeout=leetcode_data.get("timeout", 30),
                max_retries=leetcode_data.get("max_retries", 3),
                retry_delay=leetcode_data.get("retry_delay", 2),
            ),
            verifier=VerifierSettings(
                execution_timeout=verifier_data.get("execution_timeout", 5),
            ),
            claude=ClaudeSettings(
                model=claude_data.get("model"),
            ),
        )

    def validate_vault_path(self) -> bool:
        """Check if vault path is configured and exists.

        Returns:
            True if vault path is valid, False otherwise.
        """
        if not self.vault_path:
            return False

        vault = Path(self.vault_path)
        return vault.exists() and vault.is_dir()

    def get_vault_path(self) -> Optional[Path]:
        """Get vault path as Path object.

        Returns:
            Path object if valid, None otherwise.
        """
        if self.validate_vault_path():
            return Path(self.vault_path)
        return None


# Global settings instance
_settings: Optional[Settings] = None


def get_settings(config_path: Optional[str] = None) -> Settings:
    """Get or create global settings instance.

    Args:
        config_path: Optional path to config file.

    Returns:
        Settings instance.
    """
    global _settings
    if _settings is None:
        _settings = Settings.load(config_path)
    return _settings


def reload_settings(config_path: Optional[str] = None) -> Settings:
    """Force reload settings from config file.

    Args:
        config_path: Optional path to config file.

    Returns:
        New Settings instance.
    """
    global _settings
    _settings = Settings.load(config_path)
    return _settings
