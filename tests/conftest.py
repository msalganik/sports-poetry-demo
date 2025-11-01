"""Shared pytest fixtures for all tests."""

import os
import json
import pytest
from pathlib import Path
from typing import Dict, Any


@pytest.fixture
def temp_session(tmp_path):
    """Create a temporary session directory for tests.

    This fixture provides a clean temporary directory for each test
    and automatically cleans up after the test completes.
    """
    session_dir = tmp_path / "test_session"
    session_dir.mkdir()
    yield session_dir
    # Cleanup happens automatically via tmp_path


@pytest.fixture
def api_key():
    """Load Together.ai API key from environment or file.

    Tests that require an API key should use this fixture and will be
    automatically skipped if no key is available.
    """
    # Try environment variable first
    key = os.getenv("TOGETHER_API_KEY")

    # Try file if env var not set
    if not key:
        key_file = Path.home() / "together_api_key.txt"
        if key_file.exists():
            key = key_file.read_text().strip()

    # Skip test if no key available
    if not key:
        pytest.skip("No API key available (set TOGETHER_API_KEY or ~/together_api_key.txt)")

    return key


@pytest.fixture
def sample_config():
    """Provide a sample config dict for testing."""
    return {
        "sports": ["basketball", "soccer", "tennis"],
        "timestamp": "2025-11-01T18:00:00Z",
        "session_id": "test_session",
        "retry_enabled": True,
        "generation_mode": "template",
        "llm_provider": "together",
        "llm_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
    }


@pytest.fixture
def config_file(tmp_path, sample_config):
    """Create a temporary config.json file.

    Returns the path to the config file. The config uses template mode
    by default but can be modified in tests.
    """
    config_path = tmp_path / "config.json"
    with open(config_path, "w") as f:
        json.dump(sample_config, f, indent=2)
    return config_path


@pytest.fixture
def mock_output_dir(tmp_path):
    """Create a mock output directory structure."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


def create_test_config(
    sports: list,
    session_id: str = "test_session",
    mode: str = "template",
    api_key: str = None
) -> Dict[str, Any]:
    """Helper function to create test config dictionaries.

    Args:
        sports: List of sports to generate poems for
        session_id: Session identifier
        mode: "template" or "llm"
        api_key: API key for LLM mode (optional)

    Returns:
        Config dictionary
    """
    config = {
        "sports": sports,
        "timestamp": "2025-11-01T18:00:00Z",
        "session_id": session_id,
        "retry_enabled": True,
        "generation_mode": mode,
        "llm_provider": "together",
        "llm_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
    }

    # Set API key in environment if provided
    if api_key:
        os.environ["TOGETHER_API_KEY"] = api_key

    return config


# Make helper function available to all tests
pytest.create_test_config = create_test_config
