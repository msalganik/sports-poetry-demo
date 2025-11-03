"""Unit tests for config_builder module."""

import pytest
import json
from pathlib import Path
from config_builder import ConfigBuilder, ConfigValidationError, compute_changes_from_default


class TestConfigBuilder:
    """Tests for ConfigBuilder class."""

    def test_default_config(self):
        """Test that default config has expected values."""
        builder = ConfigBuilder()
        assert builder.config["sports"] == []
        assert builder.config["retry_enabled"] is True
        assert builder.config["generation_mode"] == "template"
        assert builder.config["llm_provider"] == "together"

    def test_with_sports_valid(self):
        """Test adding valid sports list."""
        builder = ConfigBuilder()
        builder.with_sports(["basketball", "soccer", "tennis"])
        assert builder.config["sports"] == ["basketball", "soccer", "tennis"]

    def test_with_sports_normalizes_case(self):
        """Test that sports names are normalized to lowercase."""
        builder = ConfigBuilder()
        builder.with_sports(["BASKETBALL", "Soccer", "TenNis"])
        assert builder.config["sports"] == ["basketball", "soccer", "tennis"]

    def test_with_sports_strips_whitespace(self):
        """Test that whitespace is stripped from sport names."""
        builder = ConfigBuilder()
        builder.with_sports([" basketball ", "  soccer", "tennis  "])
        assert builder.config["sports"] == ["basketball", "soccer", "tennis"]

    def test_with_sports_too_few(self):
        """Test that fewer than 3 sports raises error."""
        builder = ConfigBuilder()
        with pytest.raises(ConfigValidationError, match="at least 3 sports"):
            builder.with_sports(["basketball", "soccer"])

    def test_with_sports_too_many(self):
        """Test that more than 5 sports raises error."""
        builder = ConfigBuilder()
        with pytest.raises(ConfigValidationError, match="more than 5 sports"):
            builder.with_sports(["a", "b", "c", "d", "e", "f"])

    def test_with_sports_duplicates(self):
        """Test that duplicate sports raise error."""
        builder = ConfigBuilder()
        with pytest.raises(ConfigValidationError, match="duplicates"):
            builder.with_sports(["basketball", "soccer", "basketball"])

    def test_with_sports_empty_string(self):
        """Test that empty sport names raise error."""
        builder = ConfigBuilder()
        with pytest.raises(ConfigValidationError, match="empty values"):
            builder.with_sports(["basketball", "", "tennis"])

    def test_with_sports_not_list(self):
        """Test that non-list input raises error."""
        builder = ConfigBuilder()
        with pytest.raises(ConfigValidationError, match="must be a list"):
            builder.with_sports("basketball,soccer,tennis")

    def test_with_session_id_custom(self):
        """Test setting custom session ID."""
        builder = ConfigBuilder()
        builder.with_session_id("test_session_123")
        assert builder.config["session_id"] == "test_session_123"

    def test_with_session_id_auto_generate(self):
        """Test auto-generating session ID."""
        builder = ConfigBuilder()
        builder.with_session_id()
        assert builder.config["session_id"] is not None
        assert builder.config["session_id"].startswith("session_")

    def test_with_timestamp_custom(self):
        """Test setting custom timestamp."""
        builder = ConfigBuilder()
        timestamp = "2025-01-01T12:00:00Z"
        builder.with_timestamp(timestamp)
        assert builder.config["timestamp"] == timestamp

    def test_with_timestamp_auto_generate(self):
        """Test auto-generating timestamp."""
        builder = ConfigBuilder()
        builder.with_timestamp()
        assert builder.config["timestamp"] is not None
        assert "Z" in builder.config["timestamp"]

    def test_with_retry_enabled(self):
        """Test enabling retry."""
        builder = ConfigBuilder()
        builder.with_retry(True)
        assert builder.config["retry_enabled"] is True

    def test_with_retry_disabled(self):
        """Test disabling retry."""
        builder = ConfigBuilder()
        builder.with_retry(False)
        assert builder.config["retry_enabled"] is False

    def test_with_generation_mode_template(self):
        """Test setting template generation mode."""
        builder = ConfigBuilder()
        builder.with_generation_mode("template")
        assert builder.config["generation_mode"] == "template"

    def test_with_generation_mode_llm(self):
        """Test setting LLM generation mode."""
        builder = ConfigBuilder()
        builder.with_generation_mode("llm")
        assert builder.config["generation_mode"] == "llm"

    def test_with_generation_mode_invalid(self):
        """Test that invalid generation mode raises error."""
        builder = ConfigBuilder()
        with pytest.raises(ConfigValidationError, match="Invalid generation mode"):
            builder.with_generation_mode("invalid")

    def test_with_llm_provider_together(self):
        """Test setting Together.ai provider."""
        builder = ConfigBuilder()
        builder.with_llm_provider("together")
        assert builder.config["llm_provider"] == "together"

    def test_with_llm_provider_huggingface(self):
        """Test setting HuggingFace provider."""
        builder = ConfigBuilder()
        builder.with_llm_provider("huggingface")
        assert builder.config["llm_provider"] == "huggingface"

    def test_with_llm_provider_invalid(self):
        """Test that invalid LLM provider raises error."""
        builder = ConfigBuilder()
        with pytest.raises(ConfigValidationError, match="Invalid LLM provider"):
            builder.with_llm_provider("openai")

    def test_with_llm_model(self):
        """Test setting LLM model."""
        builder = ConfigBuilder()
        builder.with_llm_model("custom-model-name")
        assert builder.config["llm_model"] == "custom-model-name"

    def test_method_chaining(self):
        """Test that methods support chaining."""
        builder = ConfigBuilder()
        result = (builder
                  .with_sports(["basketball", "soccer", "tennis"])
                  .with_generation_mode("llm")
                  .with_retry(False))
        assert result is builder
        assert builder.config["sports"] == ["basketball", "soccer", "tennis"]
        assert builder.config["generation_mode"] == "llm"
        assert builder.config["retry_enabled"] is False

    def test_validate_success(self):
        """Test that valid config passes validation."""
        builder = ConfigBuilder()
        builder.with_sports(["basketball", "soccer", "tennis"])
        builder.with_session_id("test")
        builder.with_timestamp("2025-01-01T12:00:00Z")
        config = builder.validate()
        assert config["sports"] == ["basketball", "soccer", "tennis"]

    def test_validate_missing_sports(self):
        """Test that validation fails without sports."""
        builder = ConfigBuilder()
        builder.with_session_id("test")
        builder.with_timestamp("2025-01-01T12:00:00Z")
        with pytest.raises(ConfigValidationError, match="Sports list is required"):
            builder.validate()

    def test_validate_missing_session_id(self):
        """Test that validation fails without session ID."""
        builder = ConfigBuilder()
        builder.with_sports(["basketball", "soccer", "tennis"])
        builder.with_timestamp("2025-01-01T12:00:00Z")
        with pytest.raises(ConfigValidationError, match="Session ID is required"):
            builder.validate()

    def test_validate_missing_timestamp(self):
        """Test that validation fails without timestamp."""
        builder = ConfigBuilder()
        builder.with_sports(["basketball", "soccer", "tennis"])
        builder.with_session_id("test")
        with pytest.raises(ConfigValidationError, match="Timestamp is required"):
            builder.validate()

    def test_validate_llm_mode_requires_provider(self):
        """Test that LLM mode requires provider."""
        builder = ConfigBuilder()
        builder.with_sports(["basketball", "soccer", "tennis"])
        builder.with_session_id("test")
        builder.with_timestamp("2025-01-01T12:00:00Z")
        builder.with_generation_mode("llm")
        builder.config["llm_provider"] = None  # Manually break it
        with pytest.raises(ConfigValidationError, match="LLM provider is required"):
            builder.validate()

    def test_validate_llm_mode_requires_model(self):
        """Test that LLM mode requires model."""
        builder = ConfigBuilder()
        builder.with_sports(["basketball", "soccer", "tennis"])
        builder.with_session_id("test")
        builder.with_timestamp("2025-01-01T12:00:00Z")
        builder.with_generation_mode("llm")
        builder.config["llm_model"] = None  # Manually break it
        with pytest.raises(ConfigValidationError, match="LLM model is required"):
            builder.validate()

    def test_build_auto_generates_fields(self):
        """Test that build auto-generates missing fields."""
        builder = ConfigBuilder()
        builder.with_sports(["basketball", "soccer", "tennis"])
        config = builder.build()
        assert config["session_id"] is not None
        assert config["timestamp"] is not None
        assert config["sports"] == ["basketball", "soccer", "tennis"]

    def test_build_preserves_explicit_fields(self):
        """Test that build preserves explicitly set fields."""
        builder = ConfigBuilder()
        builder.with_sports(["basketball", "soccer", "tennis"])
        builder.with_session_id("custom_session")
        builder.with_timestamp("2025-01-01T12:00:00Z")
        config = builder.build()
        assert config["session_id"] == "custom_session"
        assert config["timestamp"] == "2025-01-01T12:00:00Z"

    def test_save_creates_file(self, tmp_path, monkeypatch):
        """Test that save creates a config file."""
        monkeypatch.chdir(tmp_path)
        # Create default config
        default_config = {
            "sports": ["basketball", "soccer", "tennis"],
            "session_id": None,
            "timestamp": None,
            "retry_enabled": True,
            "generation_mode": "template",
            "llm_provider": "together",
            "llm_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
        }
        default_path = tmp_path / "config.default.json"
        with open(default_path, "w") as f:
            json.dump(default_config, f)

        config_path = tmp_path / "test_config.json"
        builder = ConfigBuilder()
        builder.with_sports(["basketball", "soccer", "tennis"])
        path = builder.save(str(config_path), reason="Test save creates file", user="test")

        assert path.exists()
        with open(path, "r") as f:
            data = json.load(f)
        assert data["sports"] == ["basketball", "soccer", "tennis"]

    def test_save_default_path(self, tmp_path, monkeypatch):
        """Test that save uses default path."""
        monkeypatch.chdir(tmp_path)
        # Create default config
        default_config = {
            "sports": ["basketball", "soccer", "tennis"],
            "session_id": None,
            "timestamp": None,
            "retry_enabled": True,
            "generation_mode": "template",
            "llm_provider": "together",
            "llm_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
        }
        default_path = tmp_path / "config.default.json"
        with open(default_path, "w") as f:
            json.dump(default_config, f)

        builder = ConfigBuilder()
        builder.with_sports(["basketball", "soccer", "tennis"])
        path = builder.save(reason="Test default path", user="test")

        assert path.name == "config.json"
        assert path.exists()

    def test_from_dict(self):
        """Test creating builder from dictionary."""
        data = {
            "sports": ["basketball", "soccer", "tennis"],
            "session_id": "test_session",
            "timestamp": "2025-01-01T12:00:00Z",
            "retry_enabled": False,
            "generation_mode": "llm",
            "llm_provider": "together",
            "llm_model": "test-model"
        }
        builder = ConfigBuilder.from_dict(data)
        assert builder.config["sports"] == ["basketball", "soccer", "tennis"]
        assert builder.config["retry_enabled"] is False
        assert builder.config["generation_mode"] == "llm"

    def test_load_existing_config(self, tmp_path):
        """Test loading existing config file."""
        config_path = tmp_path / "test_config.json"
        data = {
            "sports": ["hockey", "volleyball", "swimming"],
            "session_id": "loaded_session",
            "timestamp": "2025-01-01T12:00:00Z",
            "retry_enabled": True,
            "generation_mode": "template",
            "llm_provider": "together",
            "llm_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
        }
        with open(config_path, "w") as f:
            json.dump(data, f)

        builder = ConfigBuilder.load(str(config_path))
        assert builder.config["sports"] == ["hockey", "volleyball", "swimming"]
        assert builder.config["session_id"] == "loaded_session"

    def test_load_default_exists(self, tmp_path, monkeypatch):
        """Test loading default config successfully."""
        monkeypatch.chdir(tmp_path)
        # Create a default config
        default_config = {
            "sports": ["basketball", "soccer", "tennis"],
            "session_id": None,
            "timestamp": None,
            "retry_enabled": True,
            "generation_mode": "template",
            "llm_provider": "together",
            "llm_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
        }
        default_path = tmp_path / "config.default.json"
        with open(default_path, "w") as f:
            json.dump(default_config, f)

        builder = ConfigBuilder.load_default(str(default_path))
        assert builder.config["sports"] == ["basketball", "soccer", "tennis"]
        assert builder.config["generation_mode"] == "template"

    def test_load_default_missing(self, tmp_path):
        """Test that load_default fails with clear error if default missing."""
        missing_path = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError, match="Default config not found"):
            ConfigBuilder.load_default(str(missing_path))

    def test_save_with_changelog_all_defaults(self, tmp_path, monkeypatch):
        """Test changelog when using all defaults."""
        monkeypatch.chdir(tmp_path)
        # Create default config
        default_config = {
            "sports": ["basketball", "soccer", "tennis"],
            "session_id": None,
            "timestamp": None,
            "retry_enabled": True,
            "generation_mode": "template",
            "llm_provider": "together",
            "llm_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
        }
        default_path = tmp_path / "config.default.json"
        with open(default_path, "w") as f:
            json.dump(default_config, f)

        # Create config using all defaults
        builder = ConfigBuilder.load_default(str(default_path))
        config_path = tmp_path / "config.json"
        builder.save_with_changelog(
            str(config_path),
            reason="Initial configuration using all defaults",
            user="test"
        )

        # Check that changelog was created
        session_id = builder.config["session_id"]
        changelog_path = tmp_path / "output" / session_id / "config.changelog.json"
        assert changelog_path.exists()

        with open(changelog_path) as f:
            changelog = json.load(f)

        assert changelog["changed_from_default"] == []
        assert changelog["changes"] == {}
        assert changelog["reason"] == "Initial configuration using all defaults"
        assert changelog["user"] == "test"

    def test_save_with_changelog_sports_changed(self, tmp_path, monkeypatch):
        """Test changelog when sports are changed."""
        monkeypatch.chdir(tmp_path)
        # Create default config
        default_config = {
            "sports": ["basketball", "soccer", "tennis"],
            "session_id": None,
            "timestamp": None,
            "retry_enabled": True,
            "generation_mode": "template",
            "llm_provider": "together",
            "llm_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
        }
        default_path = tmp_path / "config.default.json"
        with open(default_path, "w") as f:
            json.dump(default_config, f)

        # Create config with different sports
        builder = ConfigBuilder.load_default(str(default_path))
        builder.with_sports(["hockey", "swimming", "volleyball"])
        config_path = tmp_path / "config.json"
        builder.save_with_changelog(
            str(config_path),
            reason="User changed sports selection",
            user="test"
        )

        # Check changelog
        session_id = builder.config["session_id"]
        changelog_path = tmp_path / "output" / session_id / "config.changelog.json"

        with open(changelog_path) as f:
            changelog = json.load(f)

        assert changelog["changed_from_default"] == ["sports"]
        assert changelog["changes"]["sports"]["old"] == ["basketball", "soccer", "tennis"]
        assert changelog["changes"]["sports"]["new"] == ["hockey", "swimming", "volleyball"]

    def test_save_with_changelog_multiple_changes(self, tmp_path, monkeypatch):
        """Test changelog when multiple fields change."""
        monkeypatch.chdir(tmp_path)
        # Create default config
        default_config = {
            "sports": ["basketball", "soccer", "tennis"],
            "session_id": None,
            "timestamp": None,
            "retry_enabled": True,
            "generation_mode": "template",
            "llm_provider": "together",
            "llm_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
        }
        default_path = tmp_path / "config.default.json"
        with open(default_path, "w") as f:
            json.dump(default_config, f)

        # Create config with multiple changes
        builder = ConfigBuilder.load_default(str(default_path))
        builder.with_sports(["hockey", "swimming", "volleyball"])
        builder.with_generation_mode("llm")
        builder.with_llm_model("different-model")
        config_path = tmp_path / "config.json"
        builder.save_with_changelog(
            str(config_path),
            reason="User changed sports and enabled LLM mode",
            user="claude_code"
        )

        # Check changelog
        session_id = builder.config["session_id"]
        changelog_path = tmp_path / "output" / session_id / "config.changelog.json"

        with open(changelog_path) as f:
            changelog = json.load(f)

        assert "sports" in changelog["changed_from_default"]
        assert "generation_mode" in changelog["changed_from_default"]
        assert "llm_model" in changelog["changed_from_default"]
        assert len(changelog["changed_from_default"]) == 3

    def test_save_with_changelog_no_reason(self, tmp_path, monkeypatch):
        """Test that save_with_changelog provides default reason when None."""
        monkeypatch.chdir(tmp_path)
        # Create default config
        default_config = {
            "sports": ["basketball", "soccer", "tennis"],
            "session_id": None,
            "timestamp": None,
            "retry_enabled": True,
            "generation_mode": "template",
            "llm_provider": "together",
            "llm_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
        }
        default_path = tmp_path / "config.default.json"
        with open(default_path, "w") as f:
            json.dump(default_config, f)

        builder = ConfigBuilder.load_default(str(default_path))
        config_path = tmp_path / "config.json"

        # Should not raise error, should use default reason
        builder.save_with_changelog(str(config_path), reason=None, user="test")

        # Verify changelog was created with default reason
        session_id = builder.config["session_id"]
        changelog_path = tmp_path / "output" / session_id / "config.changelog.json"

        with open(changelog_path) as f:
            changelog = json.load(f)

        assert changelog["reason"] == "Configuration saved"

    def test_changelog_excludes_auto_fields(self, tmp_path, monkeypatch):
        """Test that session_id and timestamp are not tracked in changes."""
        monkeypatch.chdir(tmp_path)
        # Create default config
        default_config = {
            "sports": ["basketball", "soccer", "tennis"],
            "session_id": None,
            "timestamp": None,
            "retry_enabled": True,
            "generation_mode": "template",
            "llm_provider": "together",
            "llm_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
        }
        default_path = tmp_path / "config.default.json"
        with open(default_path, "w") as f:
            json.dump(default_config, f)

        builder = ConfigBuilder.load_default(str(default_path))
        config_path = tmp_path / "config.json"
        builder.save_with_changelog(
            str(config_path),
            reason="Test auto-field exclusion",
            user="test"
        )

        # Check changelog
        session_id = builder.config["session_id"]
        changelog_path = tmp_path / "output" / session_id / "config.changelog.json"

        with open(changelog_path) as f:
            changelog = json.load(f)

        assert "session_id" not in changelog["changed_from_default"]
        assert "timestamp" not in changelog["changed_from_default"]
        assert "session_id" not in changelog["changes"]
        assert "timestamp" not in changelog["changes"]

    def test_changelog_location(self, tmp_path, monkeypatch):
        """Test that changelog is written to output/{session_id}/."""
        monkeypatch.chdir(tmp_path)
        # Create default config
        default_config = {
            "sports": ["basketball", "soccer", "tennis"],
            "session_id": None,
            "timestamp": None,
            "retry_enabled": True,
            "generation_mode": "template",
            "llm_provider": "together",
            "llm_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
        }
        default_path = tmp_path / "config.default.json"
        with open(default_path, "w") as f:
            json.dump(default_config, f)

        builder = ConfigBuilder.load_default(str(default_path))
        config_path = tmp_path / "config.json"
        builder.save_with_changelog(
            str(config_path),
            reason="Test changelog location",
            user="test"
        )

        session_id = builder.config["session_id"]
        expected_path = tmp_path / "output" / session_id / "config.changelog.json"
        assert expected_path.exists()

    def test_changelog_required_fields(self, tmp_path, monkeypatch):
        """Test that changelog contains all required fields."""
        monkeypatch.chdir(tmp_path)
        # Create default config
        default_config = {
            "sports": ["basketball", "soccer", "tennis"],
            "session_id": None,
            "timestamp": None,
            "retry_enabled": True,
            "generation_mode": "template",
            "llm_provider": "together",
            "llm_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
        }
        default_path = tmp_path / "config.default.json"
        with open(default_path, "w") as f:
            json.dump(default_config, f)

        builder = ConfigBuilder.load_default(str(default_path))
        config_path = tmp_path / "config.json"
        builder.save_with_changelog(
            str(config_path),
            reason="Test required fields",
            user="test"
        )

        session_id = builder.config["session_id"]
        changelog_path = tmp_path / "output" / session_id / "config.changelog.json"

        with open(changelog_path) as f:
            changelog = json.load(f)

        # Verify all required fields are present
        assert "timestamp" in changelog
        assert "session_id" in changelog
        assert "user" in changelog
        assert "reason" in changelog
        assert "changed_from_default" in changelog
        assert "changes" in changelog


class TestComputeChangesFromDefault:
    """Tests for compute_changes_from_default helper function."""

    def test_no_changes(self):
        """Test when config matches default exactly."""
        default = {
            "sports": ["basketball", "soccer", "tennis"],
            "session_id": "test",
            "timestamp": "2025-01-01T12:00:00Z",
            "generation_mode": "template"
        }
        new = default.copy()

        changed, changes = compute_changes_from_default(default, new)

        # session_id and timestamp are excluded, so no changes
        assert changed == []
        assert changes == {}

    def test_single_change(self):
        """Test when one field changes."""
        default = {
            "sports": ["basketball", "soccer", "tennis"],
            "session_id": "test",
            "timestamp": "2025-01-01T12:00:00Z",
            "generation_mode": "template"
        }
        new = default.copy()
        new["generation_mode"] = "llm"

        changed, changes = compute_changes_from_default(default, new)

        assert changed == ["generation_mode"]
        assert changes["generation_mode"]["old"] == "template"
        assert changes["generation_mode"]["new"] == "llm"

    def test_multiple_changes(self):
        """Test when multiple fields change."""
        default = {
            "sports": ["basketball", "soccer", "tennis"],
            "session_id": "test",
            "timestamp": "2025-01-01T12:00:00Z",
            "generation_mode": "template",
            "retry_enabled": True
        }
        new = default.copy()
        new["sports"] = ["hockey", "swimming", "volleyball"]
        new["generation_mode"] = "llm"

        changed, changes = compute_changes_from_default(default, new)

        assert "sports" in changed
        assert "generation_mode" in changed
        assert len(changed) == 2

    def test_excludes_session_id_and_timestamp(self):
        """Test that session_id and timestamp changes are excluded."""
        default = {
            "sports": ["basketball", "soccer", "tennis"],
            "session_id": "session1",
            "timestamp": "2025-01-01T12:00:00Z",
            "generation_mode": "template"
        }
        new = default.copy()
        new["session_id"] = "session2"
        new["timestamp"] = "2025-01-02T12:00:00Z"

        changed, changes = compute_changes_from_default(default, new)

        assert "session_id" not in changed
        assert "timestamp" not in changed
        assert changed == []
        assert changes == {}


class TestConfigBuilderIntegration:
    """Integration tests for typical usage patterns."""

    def test_template_mode_workflow(self, tmp_path, monkeypatch):
        """Test complete workflow for template mode config."""
        monkeypatch.chdir(tmp_path)
        # Create default config
        default_config = {
            "sports": ["basketball", "soccer", "tennis"],
            "session_id": None,
            "timestamp": None,
            "retry_enabled": True,
            "generation_mode": "template",
            "llm_provider": "together",
            "llm_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
        }
        default_path = tmp_path / "config.default.json"
        with open(default_path, "w") as f:
            json.dump(default_config, f)

        config_path = tmp_path / "config.json"
        # Use load_default() pattern (matches documentation)
        builder = ConfigBuilder.load_default(str(default_path))
        # Using default sports, so no changes needed
        path = builder.save(str(config_path), reason="Test template mode workflow", user="test")

        # Verify file contents
        with open(path, "r") as f:
            config = json.load(f)

        assert config["sports"] == ["basketball", "soccer", "tennis"]
        assert config["generation_mode"] == "template"
        assert config["session_id"].startswith("session_")
        assert "Z" in config["timestamp"]

    def test_llm_mode_workflow(self, tmp_path, monkeypatch):
        """Test complete workflow for LLM mode config."""
        monkeypatch.chdir(tmp_path)
        # Create default config
        default_config = {
            "sports": ["basketball", "soccer", "tennis"],
            "session_id": None,
            "timestamp": None,
            "retry_enabled": True,
            "generation_mode": "template",
            "llm_provider": "together",
            "llm_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
        }
        default_path = tmp_path / "config.default.json"
        with open(default_path, "w") as f:
            json.dump(default_config, f)

        config_path = tmp_path / "config.json"
        # Use load_default() pattern (matches documentation)
        builder = ConfigBuilder.load_default(str(default_path))
        builder.with_sports(["hockey", "volleyball", "swimming", "baseball"])
        builder.with_generation_mode("llm")
        # llm_provider and llm_model already match defaults, no need to set
        path = builder.save(str(config_path), reason="Test LLM mode workflow", user="test")

        # Verify file contents
        with open(path, "r") as f:
            config = json.load(f)

        assert config["sports"] == ["hockey", "volleyball", "swimming", "baseball"]
        assert config["generation_mode"] == "llm"
        assert config["llm_provider"] == "together"
        assert config["llm_model"] == "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"

    def test_modify_and_resave(self, tmp_path, monkeypatch):
        """Test loading, modifying, and resaving config."""
        monkeypatch.chdir(tmp_path)
        # Create default config
        default_config = {
            "sports": ["basketball", "soccer", "tennis"],
            "session_id": None,
            "timestamp": None,
            "retry_enabled": True,
            "generation_mode": "template",
            "llm_provider": "together",
            "llm_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
        }
        default_path = tmp_path / "config.default.json"
        with open(default_path, "w") as f:
            json.dump(default_config, f)

        config_path = tmp_path / "config.json"

        # Create initial config using load_default() pattern
        builder1 = ConfigBuilder.load_default(str(default_path))
        # Using default sports, no changes needed
        builder1.save(str(config_path), reason="Initial config", user="test")

        # Load and modify
        builder2 = ConfigBuilder.load(str(config_path))
        builder2.with_generation_mode("llm")
        builder2.with_llm_provider("together")
        builder2.save(str(config_path), reason="Enable LLM mode", user="test")

        # Verify modifications
        with open(config_path, "r") as f:
            config = json.load(f)

        assert config["sports"] == ["basketball", "soccer", "tennis"]
        assert config["generation_mode"] == "llm"
