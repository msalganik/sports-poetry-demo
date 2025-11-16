"""
End-to-End Output Validation Tests

Approach 1: Test the OUTCOMES of skill execution, not the process.

This approach:
- Simulates the expected workflow the skill should execute
- Validates that outputs meet requirements
- Doesn't test Claude's decision-making
- Fast, deterministic, reliable

Use when: You want to ensure the skill utilities produce correct outputs
Don't use when: You need to test Claude's actual decision-making
"""

import pytest
import json
import os
import stat
import subprocess
from pathlib import Path
from datetime import datetime
import tempfile
import shutil
import sys

# Add skill_helpers to path
sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "skills" / "create_config"))

from skill_helpers import check_api_key, create_generator_script
from config_builder import ConfigBuilder


class TestE2EOutputValidation:
    """
    End-to-end tests that validate the complete workflow outputs.

    These tests simulate what the skill SHOULD do and verify the results.
    """

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        temp_dir = tempfile.mkdtemp()
        output_dir = Path(temp_dir) / "output" / "configs"
        output_dir.mkdir(parents=True, exist_ok=True)

        yield output_dir

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_complete_template_mode_workflow(self, temp_output_dir):
        """
        Test the complete workflow for template mode.

        This simulates what Claude should do when user says:
        "Create a config for basketball, soccer, and tennis"
        """
        # === SIMULATE SKILL EXECUTION ===

        # Input (what user provides)
        sports = ["basketball", "soccer", "tennis"]
        mode = "template"

        # Step 1: Create config using ConfigBuilder
        builder = ConfigBuilder.load_default()
        builder.with_sports(sports)

        # Step 2: Generate timestamp and paths
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        config_path = temp_output_dir / f"config_{timestamp}.json"
        script_path = temp_output_dir / f"generate_config_{timestamp}.py"

        # Step 3: Save config file
        saved_config_path = builder.save(str(config_path))

        # Step 4: Create generator script
        script = create_generator_script(
            sports=sports,
            mode=mode,
            provider="together",
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            retry=True,
            timestamp=timestamp
        )
        script_path.write_text(script)

        # Step 5: Make script executable
        os.chmod(script_path, os.stat(script_path).st_mode | stat.S_IEXEC)

        # === VALIDATE OUTCOMES ===

        # Outcome 1: Both files should exist
        assert config_path.exists(), "Config file should be created"
        assert script_path.exists(), "Generator script should be created"

        # Outcome 2: Config file should be valid JSON with correct structure
        with open(config_path) as f:
            config = json.load(f)

        assert config["sports"] == sports, "Sports list should match input"
        assert config["generation_mode"] == "template", "Should use template mode"
        assert config["retry_enabled"] is True, "Retry should be enabled by default"
        assert "session_id" not in config, "Session ID should not be in input config"
        assert "llm" not in config, "Template mode should not have LLM config"

        # Outcome 3: Generator script should be executable
        assert os.access(script_path, os.X_OK), "Generator script should be executable"

        # Outcome 4: Generator script should be valid Python
        compile(script_path.read_text(), str(script_path), 'exec')

        # Outcome 5: Generator script should be runnable
        # (This tests reproducibility - in practice the script creates new configs)
        # Note: We verify the script is valid Python above via compile()
        # Actually running it requires matching the exact directory structure,
        # which is tested in manual E2E tests

        # Verify script contains the correct code structure
        script_content = script_path.read_text()
        assert "ConfigBuilder.load_default()" in script_content
        assert f"with_sports({sports!r})" in script_content
        assert "datetime.now().strftime" in script_content
        assert "new_config_path = " in script_content

    def test_complete_llm_mode_workflow_with_api_key(self, temp_output_dir, monkeypatch):
        """
        Test the complete workflow for LLM mode with API key.

        This simulates what Claude should do when user says:
        "Create an LLM mode config for hockey, swimming, volleyball"
        """
        # Mock API key
        monkeypatch.setenv("TOGETHER_API_KEY", "test-key-12345678901234567890123456789012")

        # === SIMULATE SKILL EXECUTION ===

        sports = ["hockey", "swimming", "volleyball"]
        provider = "together"
        model = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"

        # Step 1: Check for API key (skill should do this)
        api_key = check_api_key(provider)
        assert api_key is not None, "API key check should succeed"

        # Step 2: Create LLM mode config
        builder = ConfigBuilder.load_default()
        builder.with_sports(sports)
        builder.with_generation_mode("llm")
        builder.with_llm_provider(provider)
        builder.with_llm_model(model)

        # Step 3: Save files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        config_path = temp_output_dir / f"config_{timestamp}.json"
        script_path = temp_output_dir / f"generate_config_{timestamp}.py"

        builder.save(str(config_path))

        script = create_generator_script(
            sports=sports,
            mode="llm",
            provider=provider,
            model=model,
            retry=True,
            timestamp=timestamp
        )
        script_path.write_text(script)
        os.chmod(script_path, os.stat(script_path).st_mode | stat.S_IEXEC)

        # === VALIDATE OUTCOMES ===

        # Outcome 1: Config should have LLM settings
        with open(config_path) as f:
            config = json.load(f)

        assert config["generation_mode"] == "llm"
        assert config["llm"]["provider"] == provider
        assert config["llm"]["model"] == model

        # Outcome 2: Generator script should include LLM builder calls
        script_content = script_path.read_text()
        assert 'with_generation_mode("llm")' in script_content
        assert f'with_llm_provider("{provider}")' in script_content
        assert f'with_llm_model("{model}")' in script_content

    def test_validation_error_handling(self, temp_output_dir):
        """
        Test that validation errors are caught and reported clearly.

        This simulates what happens when user provides invalid input:
        "Create a config for basketball and soccer" (only 2 sports)
        """
        from config_builder import ConfigValidationError

        # === SIMULATE SKILL EXECUTION ===

        sports = ["basketball", "soccer"]  # Only 2, need 3-5

        builder = ConfigBuilder.load_default()

        # Skill should catch this error and report to user
        with pytest.raises(ConfigValidationError) as exc_info:
            builder.with_sports(sports)

        # === VALIDATE ERROR HANDLING ===

        error_message = str(exc_info.value)

        # Outcome 1: Error message should be helpful
        assert "3" in error_message or "at least" in error_message, \
            "Error should mention minimum count"
        assert "2" in error_message or "got 2" in error_message, \
            "Error should mention actual count"

        # The skill should:
        # 1. Catch this error
        # 2. Report: "You provided 2 sports, but we need 3-5"
        # 3. Suggest adding one more sport
        # 4. Wait for user correction
        # 5. Retry with corrected input

        # Corrected input (what skill should do after user provides third sport)
        corrected_sports = ["basketball", "soccer", "tennis"]
        builder.with_sports(corrected_sports)  # Should succeed

        # Verify correction worked
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        config_path = temp_output_dir / f"config_{timestamp}.json"
        builder.save(str(config_path))

        with open(config_path) as f:
            config = json.load(f)

        assert config["sports"] == corrected_sports


class TestE2EPerformance:
    """Test that the workflow completes quickly."""

    @pytest.fixture
    def temp_output_dir(self):
        temp_dir = tempfile.mkdtemp()
        output_dir = Path(temp_dir) / "output" / "configs"
        output_dir.mkdir(parents=True, exist_ok=True)
        yield output_dir
        shutil.rmtree(temp_dir)

    def test_workflow_performance(self, temp_output_dir):
        """
        Test that the complete workflow finishes quickly.

        Acceptance criteria: Should complete in <5 seconds
        """
        import time

        start = time.time()

        # Execute complete workflow
        builder = ConfigBuilder.load_default()
        builder.with_sports(["basketball", "soccer", "tennis"])

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        config_path = temp_output_dir / f"config_{timestamp}.json"
        script_path = temp_output_dir / f"generate_config_{timestamp}.py"

        builder.save(str(config_path))

        script = create_generator_script(
            sports=["basketball", "soccer", "tennis"],
            mode="template",
            provider="together",
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            retry=True,
            timestamp=timestamp
        )
        script_path.write_text(script)
        os.chmod(script_path, os.stat(script_path).st_mode | stat.S_IEXEC)

        elapsed = time.time() - start

        # Should complete quickly (well under 5 seconds)
        assert elapsed < 5.0, f"Workflow took {elapsed:.2f}s, should be <5s"
        assert elapsed < 1.0, f"Workflow took {elapsed:.2f}s, should be <1s for template mode"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
