#!/usr/bin/env python3
"""
Configuration Builder for Sports Poetry Demo

Provides validation and generation of config files with a testable API.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any


class ConfigValidationError(Exception):
    """Raised when config validation fails."""
    pass


class ConfigBuilder:
    """Builder for creating and validating sports poetry configuration files."""

    # Valid configuration options
    VALID_GENERATION_MODES = ["template", "llm"]
    VALID_LLM_PROVIDERS = ["together", "huggingface"]
    MIN_SPORTS = 3
    MAX_SPORTS = 5

    def __init__(self):
        """Initialize a new config builder."""
        self.config = {
            "sports": [],
            "session_id": None,
            "timestamp": None,
            "retry_enabled": True,
            "generation_mode": "template",
            "llm_provider": "together",
            "llm_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
        }

    def with_sports(self, sports: List[str]) -> 'ConfigBuilder':
        """
        Set the sports list.

        Args:
            sports: List of sport names (3-5 sports)

        Returns:
            Self for method chaining

        Raises:
            ConfigValidationError: If sports list is invalid
        """
        if not isinstance(sports, list):
            raise ConfigValidationError("Sports must be a list")

        if len(sports) < self.MIN_SPORTS:
            raise ConfigValidationError(
                f"Must specify at least {self.MIN_SPORTS} sports (got {len(sports)})"
            )

        if len(sports) > self.MAX_SPORTS:
            raise ConfigValidationError(
                f"Cannot specify more than {self.MAX_SPORTS} sports (got {len(sports)})"
            )

        # Normalize sport names (lowercase, strip whitespace)
        normalized_sports = [sport.strip().lower() for sport in sports]

        # Check for duplicates
        if len(normalized_sports) != len(set(normalized_sports)):
            raise ConfigValidationError("Sports list contains duplicates")

        # Check for empty strings
        if any(not sport for sport in normalized_sports):
            raise ConfigValidationError("Sports list contains empty values")

        self.config["sports"] = normalized_sports
        return self

    def with_session_id(self, session_id: Optional[str] = None) -> 'ConfigBuilder':
        """
        Set the session ID.

        Args:
            session_id: Custom session ID, or None to auto-generate

        Returns:
            Self for method chaining
        """
        if session_id is None:
            # Auto-generate session ID with timestamp
            now = datetime.now(timezone.utc)
            session_id = now.strftime("session_%Y%m%d_%H%M%S")

        self.config["session_id"] = session_id
        return self

    def with_timestamp(self, timestamp: Optional[str] = None) -> 'ConfigBuilder':
        """
        Set the timestamp.

        Args:
            timestamp: ISO format timestamp, or None for current time

        Returns:
            Self for method chaining
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        self.config["timestamp"] = timestamp
        return self

    def with_retry(self, enabled: bool = True) -> 'ConfigBuilder':
        """
        Set retry behavior.

        Args:
            enabled: Whether to retry failed agents

        Returns:
            Self for method chaining
        """
        self.config["retry_enabled"] = enabled
        return self

    def with_generation_mode(self, mode: str) -> 'ConfigBuilder':
        """
        Set the generation mode.

        Args:
            mode: Either "template" or "llm"

        Returns:
            Self for method chaining

        Raises:
            ConfigValidationError: If mode is invalid
        """
        if mode not in self.VALID_GENERATION_MODES:
            raise ConfigValidationError(
                f"Invalid generation mode: {mode}. "
                f"Must be one of: {', '.join(self.VALID_GENERATION_MODES)}"
            )

        self.config["generation_mode"] = mode
        return self

    def with_llm_provider(self, provider: str) -> 'ConfigBuilder':
        """
        Set the LLM provider.

        Args:
            provider: Either "together" or "huggingface"

        Returns:
            Self for method chaining

        Raises:
            ConfigValidationError: If provider is invalid
        """
        if provider not in self.VALID_LLM_PROVIDERS:
            raise ConfigValidationError(
                f"Invalid LLM provider: {provider}. "
                f"Must be one of: {', '.join(self.VALID_LLM_PROVIDERS)}"
            )

        self.config["llm_provider"] = provider
        return self

    def with_llm_model(self, model: str) -> 'ConfigBuilder':
        """
        Set the LLM model.

        Args:
            model: Model identifier (provider-specific)

        Returns:
            Self for method chaining
        """
        self.config["llm_model"] = model
        return self

    def validate(self) -> Dict[str, Any]:
        """
        Validate the configuration.

        Returns:
            The validated config dictionary

        Raises:
            ConfigValidationError: If validation fails
        """
        # Check required fields
        if not self.config["sports"]:
            raise ConfigValidationError("Sports list is required")

        if self.config["session_id"] is None:
            raise ConfigValidationError("Session ID is required")

        if self.config["timestamp"] is None:
            raise ConfigValidationError("Timestamp is required")

        # Validate LLM mode requirements
        if self.config["generation_mode"] == "llm":
            if not self.config["llm_provider"]:
                raise ConfigValidationError("LLM provider is required for LLM mode")
            if not self.config["llm_model"]:
                raise ConfigValidationError("LLM model is required for LLM mode")

        return self.config

    def build(self) -> Dict[str, Any]:
        """
        Build and validate the configuration.

        Auto-generates session_id and timestamp if not set.

        Returns:
            The validated config dictionary

        Raises:
            ConfigValidationError: If validation fails
        """
        # Auto-generate missing fields
        if self.config["session_id"] is None:
            self.with_session_id()

        if self.config["timestamp"] is None:
            self.with_timestamp()

        return self.validate()

    def save(self, path: str = "config.json", reason: Optional[str] = None, user: str = "unknown") -> Path:
        """
        Build, validate, and save the configuration to a file with changelog.

        Args:
            path: Path to save the config file
            reason: Explanation of what changed and why (default: "Configuration saved")
            user: Who made the change (e.g., "claude_code", "cli", "api")

        Returns:
            Path object of the saved file

        Raises:
            ConfigValidationError: If validation fails
        """
        return self.save_with_changelog(config_path=path, reason=reason, user=user)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ConfigBuilder':
        """
        Create a ConfigBuilder from an existing config dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            New ConfigBuilder instance with the given config
        """
        builder = ConfigBuilder()
        builder.config = data.copy()
        return builder

    @staticmethod
    def load(path: str = "config.json") -> 'ConfigBuilder':
        """
        Load an existing config file.

        Args:
            path: Path to the config file

        Returns:
            New ConfigBuilder instance with the loaded config
        """
        with open(path, "r") as f:
            data = json.load(f)

        return ConfigBuilder.from_dict(data)

    @staticmethod
    def load_default(path: str = "config.default.json") -> 'ConfigBuilder':
        """
        Load the default configuration template.

        Args:
            path: Path to the default config file

        Returns:
            New ConfigBuilder instance with the default config

        Raises:
            FileNotFoundError: If config.default.json doesn't exist
            ConfigValidationError: If default config is invalid
        """
        if not Path(path).exists():
            raise FileNotFoundError(
                f"Default config not found: {path}\n"
                f"Repository may be corrupted. This file must exist."
            )
        return ConfigBuilder.load(path)

    def save_with_changelog(self,
                           config_path: str = "config.json",
                           reason: Optional[str] = None,
                           user: str = "unknown") -> Path:
        """
        Save config and write changelog to session directory.

        Args:
            config_path: Where to save config (default: config.json)
            reason: Explanation of what changed and why (default: "Configuration saved")
            user: Who made the change (e.g., "claude_code", "cli", "api")

        Returns:
            Path to saved config file

        Side effects:
            - Writes config to config_path
            - Creates output/{session_id}/ directory
            - Writes output/{session_id}/config.changelog.json

        Raises:
            ConfigValidationError: If validation fails
        """
        if reason is None:
            reason = "Configuration saved"

        # Build and validate new config
        new_config = self.build()

        # Load default config (always compare against this baseline)
        default_builder = ConfigBuilder.load_default()
        default_config = default_builder.config

        # Compute diff vs default (exclude auto-generated fields)
        changed_from_default, changes = compute_changes_from_default(
            default_config, new_config
        )

        # Save new config
        config_file_path = Path(config_path)
        with open(config_file_path, "w") as f:
            json.dump(new_config, f, indent=2)

        # Write changelog to session directory
        session_id = new_config["session_id"]
        session_dir = Path(f"output/{session_id}")
        session_dir.mkdir(parents=True, exist_ok=True)

        changelog = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "session_id": session_id,
            "user": user,
            "reason": reason,
            "changed_from_default": changed_from_default,
            "changes": changes
        }

        changelog_path = session_dir / "config.changelog.json"
        with open(changelog_path, "w") as f:
            json.dump(changelog, f, indent=2)

        return config_file_path


def compute_changes_from_default(default_config: Dict[str, Any],
                                 new_config: Dict[str, Any]) -> tuple:
    """
    Compare new config against default template.

    Args:
        default_config: The default configuration
        new_config: The new configuration to compare

    Returns:
        tuple: (changed_field_names, detailed_changes_dict)
            - changed_field_names: List of field names that changed
            - detailed_changes_dict: Dict mapping field names to {old, new} values
    """
    EXCLUDE_FIELDS = {"session_id", "timestamp"}

    changed_fields = []
    changes = {}

    for key in new_config:
        if key in EXCLUDE_FIELDS:
            continue

        default_value = default_config.get(key)
        new_value = new_config[key]

        if default_value != new_value:
            changed_fields.append(key)
            changes[key] = {
                "old": default_value,
                "new": new_value
            }

    return changed_fields, changes


def create_config_interactive() -> ConfigBuilder:
    """
    Create a config interactively via command line prompts.

    Returns:
        ConfigBuilder with user-provided values
    """
    print("Sports Poetry Configuration Builder")
    print("=" * 40)

    # Get sports
    print(f"\nEnter 3-5 sports (comma-separated):")
    sports_input = input("> ").strip()
    sports = [s.strip() for s in sports_input.split(",")]

    # Get generation mode
    print("\nGeneration mode:")
    print("  1. template (fast, deterministic)")
    print("  2. llm (creative, requires API key)")
    mode_choice = input("> ").strip()
    mode = "llm" if mode_choice == "2" else "template"

    # Build config starting from defaults
    builder = ConfigBuilder.load_default()
    builder.with_sports(sports)

    # Only set generation_mode if different from default (template)
    if mode != "template":
        builder.with_generation_mode(mode)

    if mode == "llm":
        print("\nLLM Provider:")
        print("  1. together (recommended)")
        print("  2. huggingface")
        provider_choice = input("> ").strip()
        provider = "huggingface" if provider_choice == "2" else "together"
        # Only set if different from default (together)
        if provider != "together":
            builder.with_llm_provider(provider)

    return builder


if __name__ == "__main__":
    import sys

    # Simple CLI interface
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        try:
            builder = create_config_interactive()
            path = builder.save()
            print(f"\n✓ Config saved to: {path}")
        except ConfigValidationError as e:
            print(f"\n✗ Error: {e}")
            sys.exit(1)
    else:
        print("Usage:")
        print("  python3 config_builder.py interactive")
        print("\nOr use programmatically:")
        print("  from config_builder import ConfigBuilder")
        print("  builder = ConfigBuilder()")
        print("  builder.with_sports(['basketball', 'soccer', 'tennis'])")
        print("  builder.with_generation_mode('llm')")
        print("  builder.save('config.json')")
