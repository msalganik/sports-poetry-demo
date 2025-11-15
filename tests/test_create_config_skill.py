"""
Evaluation scenarios for create_config skill refactoring.

Following evaluation-first development:
1. Run these tests BEFORE refactoring to establish baseline
2. Identify specific failure modes
3. Write minimal skill changes to pass tests
4. Iterate until all scenarios pass

These tests use a hybrid approach:
- Automated: Unit tests for utility functions
- Manual: Documented acceptance criteria for full skill flow
"""

import pytest
import json
import os
import stat
from pathlib import Path
from datetime import datetime
import tempfile
import shutil


# ==============================================================================
# Test Fixtures
# ==============================================================================

@pytest.fixture
def temp_output_dir():
    """Create temporary output directory for test configs."""
    temp_dir = tempfile.mkdtemp()
    output_dir = Path(temp_dir) / "output" / "configs"
    output_dir.mkdir(parents=True, exist_ok=True)

    yield output_dir

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_api_key(monkeypatch):
    """Mock API key in environment for testing."""
    monkeypatch.setenv("TOGETHER_API_KEY", "test-key-12345678901234567890123456789012")
    return "test-key-12345678901234567890123456789012"


@pytest.fixture
def mock_api_key_in_file(tmp_path):
    """Mock API key in .claude/claude.local.md file."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)

    local_md = claude_dir / "claude.local.md"
    local_md.write_text("""
# Local Configuration

TOGETHER_API_KEY: test-key-from-file-1234567890
HUGGINGFACE_API_TOKEN: hf-test-token-1234567890
""")

    return tmp_path


# ==============================================================================
# Scenario 1: Happy Path (Quick Start with Defaults)
# ==============================================================================

class TestScenario1QuickStartDefaults:
    """
    Scenario: User wants simple config with defaults.
    Input: "Create a config for basketball, soccer, and tennis"
    Expected: Template mode config created quickly, both files present.

    This is the MOST COMMON use case.
    """

    def test_config_builder_creates_valid_template_config(self, temp_output_dir):
        """
        Test that config_builder.py can create a valid template mode config.

        This tests the underlying API, not the skill itself.
        """
        from config_builder import ConfigBuilder

        # Create config using the API (what the skill should do)
        builder = ConfigBuilder.load_default()
        builder.with_sports(["basketball", "soccer", "tennis"])

        # Save to temp directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        config_path = temp_output_dir / f"config_{timestamp}.json"

        saved_path = builder.save(str(config_path))

        # Assert file was created
        assert Path(saved_path).exists()

        # Assert contents are valid
        with open(saved_path) as f:
            config = json.load(f)

        assert config["sports"] == ["basketball", "soccer", "tennis"]
        assert config["generation_mode"] == "template"
        assert config["retry_enabled"] is True
        assert "session_id" not in config  # Auto-generated at runtime
        assert "timestamp" not in config  # Auto-generated at runtime

    def test_generator_script_structure(self):
        """
        Test that a generator script has the correct structure.

        Tests skill_helpers.create_generator_script() utility function.
        """
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "skills" / "create_config"))

        from skill_helpers import create_generator_script

        # Generate script for template mode
        script = create_generator_script(
            sports=["basketball", "soccer", "tennis"],
            mode="template",
            provider="together",
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            retry=True,
            timestamp="20251115_120000"
        )

        # Expected structure of generator script
        expected_sections = [
            "#!/usr/bin/env python3",
            "from config_builder import ConfigBuilder",
            "builder = ConfigBuilder.load_default()",
            "builder.with_sports(",
            "builder.save(",
        ]

        for section in expected_sections:
            assert section in script, f"Missing expected section: {section}"

        # Script should be valid Python
        compile(script, '<string>', 'exec')

        # Script should include the sports list (Python uses single or double quotes)
        assert "['basketball', 'soccer', 'tennis']" in script or '["basketball", "soccer", "tennis"]' in script

    # MANUAL TEST: Full skill interaction
    """
    ACCEPTANCE CRITERIA (Test manually with Claude Code):

    1. User input: "Create a config for basketball, soccer, and tennis"

    2. Expected Claude behavior WITH skill:
       - Recognizes this as create_config task
       - Does NOT ask about mode (uses template default)
       - Does NOT ask about retry (uses enabled default)
       - Creates TWO files:
         * output/configs/config_{timestamp}.json
         * output/configs/generate_config_{timestamp}.json
       - Generator script is executable (chmod +x)
       - Completes in <5 seconds
       - Reports both file paths to user

    3. Expected Claude behavior WITHOUT skill:
       - May write config.json manually (slower, error-prone)
       - Likely forgets to create generator script
       - May miss session_id or timestamp fields
       - Takes longer due to trial and error

    4. Success criteria:
       ✓ Both files exist
       ✓ Config is valid JSON with correct fields
       ✓ Generator script is valid Python and executable
       ✓ Running generator script creates new config with new timestamp

    5. Run this test on: Claude Sonnet 4 (primary target)
    """


# ==============================================================================
# Scenario 2: LLM Mode with API Key Detection
# ==============================================================================

class TestScenario2LLMModeAPIKey:
    """
    Scenario: User wants LLM mode with Together.ai.
    Input: "Create an LLM mode config for hockey, swimming, volleyball"
    Expected: API key detected, LLM config created with correct settings.

    This tests CONDITIONAL logic and API key management.
    """

    def test_api_key_detection_from_environment(self, mock_api_key):
        """
        Test that API key can be detected from environment variable.

        Tests skill_helpers.check_api_key() utility function.
        """
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "skills" / "create_config"))

        from skill_helpers import check_api_key

        # Test with mocked environment variable
        key = check_api_key("together")

        assert key is not None
        assert len(key) >= 32  # Reasonable length check
        assert key == mock_api_key

    def test_api_key_detection_from_local_file(self, mock_api_key_in_file, monkeypatch):
        """
        Test that API key can be detected from .claude/claude.local.md.

        This is important when env vars aren't set.
        """
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "skills" / "create_config"))

        from skill_helpers import check_api_key

        # Change working directory to temp path with .claude/claude.local.md
        monkeypatch.chdir(mock_api_key_in_file)

        # Test skill_helpers function
        key = check_api_key("together")

        assert key is not None
        assert key == "test-key-from-file-1234567890"

    def test_config_builder_creates_valid_llm_config(self, temp_output_dir):
        """
        Test that config_builder can create LLM mode config.
        """
        from config_builder import ConfigBuilder

        builder = ConfigBuilder.load_default()
        builder.with_sports(["hockey", "swimming", "volleyball"])
        builder.with_generation_mode("llm")
        builder.with_llm_provider("together")
        builder.with_llm_model("meta-llama/Llama-3.3-70B-Instruct-Turbo-Free")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        config_path = temp_output_dir / f"config_{timestamp}.json"

        saved_path = builder.save(str(config_path))

        # Assert file and contents
        with open(saved_path) as f:
            config = json.load(f)

        assert config["sports"] == ["hockey", "swimming", "volleyball"]
        assert config["generation_mode"] == "llm"
        assert config["llm"]["provider"] == "together"
        assert config["llm"]["model"] == "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"

    # MANUAL TEST: Full skill interaction
    """
    ACCEPTANCE CRITERIA (Test manually with Claude Code):

    1. User input: "Create an LLM mode config for hockey, swimming, volleyball"

    2. Expected Claude behavior WITH skill (API key present):
       - Calls skill_helpers.check_api_key("together")
       - Finds key in environment or .claude/claude.local.md
       - Reports: "✓ API key found (32 chars)" or similar
       - Creates config with generation_mode="llm"
       - Includes llm.provider and llm.model in config
       - Generator script includes LLM builder calls

    3. Expected Claude behavior WITH skill (NO API key):
       - Calls check_api_key("together")
       - Key not found
       - Provides setup instructions:
         * Sign up at https://together.ai/
         * Get key from https://api.together.xyz/settings/api-keys
         * Set env var or add to .claude/claude.local.md
       - Offers to switch to template mode instead
       - Does NOT create broken config

    4. Expected Claude behavior WITHOUT skill:
       - May forget to check for API key
       - Creates config but orchestrator fails at runtime
       - Poor error handling

    5. Success criteria:
       ✓ API key checked before creating config
       ✓ Clear error message if key missing
       ✓ LLM config includes provider and model
       ✓ Generator script includes LLM settings

    6. Run this test on: Claude Sonnet 4
    """


# ==============================================================================
# Scenario 3: Validation and Error Recovery
# ==============================================================================

class TestScenario3ValidationAndRecovery:
    """
    Scenario: User provides invalid input (too few sports).
    Input: "Create a config for basketball and soccer"  # Only 2, need 3-5
    Expected: Clear error message, helpful suggestions, successful recovery.

    This tests ERROR HANDLING and helpful guidance.
    """

    def test_sports_count_validation_too_few(self):
        """
        Test that config_builder validates minimum sports count.

        Note: Validation happens EAGERLY in with_sports(), not later in validate().
        This is good - fail fast!
        """
        from config_builder import ConfigBuilder, ConfigValidationError

        builder = ConfigBuilder()

        # Should raise validation error immediately when setting sports
        with pytest.raises(ConfigValidationError, match="at least 3 sports"):
            builder.with_sports(["basketball", "soccer"])  # Only 2

    def test_sports_count_validation_too_many(self):
        """
        Test that config_builder validates maximum sports count.
        """
        from config_builder import ConfigBuilder, ConfigValidationError

        builder = ConfigBuilder()

        # Should raise validation error immediately
        with pytest.raises(ConfigValidationError, match="more than 5 sports"):
            builder.with_sports([
                "basketball", "soccer", "tennis",
                "volleyball", "baseball", "hockey"  # 6 sports, limit is 5
            ])

    def test_sports_validation_no_duplicates(self):
        """
        Test that duplicate sports are rejected.
        """
        from config_builder import ConfigBuilder, ConfigValidationError

        builder = ConfigBuilder()

        # Should raise validation error immediately
        with pytest.raises(ConfigValidationError, match="duplicate"):
            builder.with_sports(["basketball", "soccer", "basketball"])  # Duplicate

    def test_error_message_quality(self):
        """
        Test that error messages are helpful (not cryptic).

        Good error: "Must specify at least 3 sports (got 2)"
        Bad error: "Invalid sports list"
        """
        from config_builder import ConfigBuilder, ConfigValidationError

        builder = ConfigBuilder()

        try:
            builder.with_sports(["basketball", "soccer"])
            pytest.fail("Should have raised ConfigValidationError")
        except ConfigValidationError as e:
            error_msg = str(e)

            # Error message should include:
            # - What's wrong (too few)
            # - Expected count (3-5)
            # - Actual count (2)
            assert "3" in error_msg or "at least" in error_msg
            assert "2" in error_msg or "got 2" in error_msg

    # MANUAL TEST: Full skill interaction
    """
    ACCEPTANCE CRITERIA (Test manually with Claude Code):

    1. User input: "Create a config for basketball and soccer"

    2. Expected Claude behavior WITH skill:
       - Validates sports count (2 < 3)
       - Responds with clear error:
         "You provided 2 sports, but we need 3-5.
          Would you like to add 1 more sport?"
       - Suggests compatible sports:
         "Suggestions: tennis (complements ball sports),
                       volleyball (another ball sport),
                       baseball (similar skill set)"
       - Waits for user to add one more
       - Re-validates
       - Creates config successfully

    3. Expected Claude behavior WITHOUT skill:
       - May create config anyway (invalid)
       - Or gives cryptic error message
       - No helpful suggestions
       - User confused about what to do

    4. Alternative test case: "Create a config for winter sports"
       - If we implement category expansion:
         * Expands to: hockey, skiing, snowboarding, figure skating, curling
         * Asks user to choose 3-5 from list
       - If we skip category expansion (evaluation-first approach):
         * Claude may handle naturally without special code
         * Test to see if this is actually a problem

    5. Success criteria:
       ✓ Validation catches too few sports
       ✓ Error message is actionable (tells user what to do)
       ✓ Suggests specific sports to add
       ✓ Successfully completes after user fixes input
       ✓ Does NOT create invalid config

    6. Run this test on: Claude Sonnet 4
    """


# ==============================================================================
# Utility Function Tests (Once skill_helpers.py exists)
# ==============================================================================

class TestSkillHelpers:
    """
    Tests for utility functions in skill_helpers.py.
    """

    def test_load_sport_categories(self):
        """
        Test loading sport categories from JSON.

        Note: Returns empty dict if file doesn't exist (graceful degradation).
        """
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "skills" / "create_config"))

        from skill_helpers import load_sport_categories

        categories = load_sport_categories()

        # Should return a dict (may be empty if file doesn't exist)
        assert isinstance(categories, dict)

        # If file exists, should have expected structure
        if categories:
            assert isinstance(list(categories.values())[0], list)

    def test_expand_sport_category(self):
        """
        Test expanding category name to sport list.

        Returns empty list if category not found (graceful degradation).
        """
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "skills" / "create_config"))

        from skill_helpers import expand_sport_category

        # Test with unknown category
        sports = expand_sport_category("unknown_category_xyz")
        assert sports == []

        # If sport_categories.json exists and has winter_sports, test that
        # Otherwise just verify it returns a list
        result = expand_sport_category("winter sports")
        assert isinstance(result, list)

    def test_create_generator_script_template_mode(self):
        """
        Test generator script creation for template mode.
        """
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "skills" / "create_config"))

        from skill_helpers import create_generator_script

        script = create_generator_script(
            sports=["basketball", "soccer", "tennis"],
            mode="template",
            provider="together",
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            retry=True,
            timestamp="20251115_120000"
        )

        # Should be valid Python
        compile(script, '<string>', 'exec')

        # Should have required sections
        assert "#!/usr/bin/env python3" in script
        assert "ConfigBuilder.load_default()" in script
        assert "['basketball', 'soccer', 'tennis']" in script or '["basketball", "soccer", "tennis"]' in script

        # Template mode should NOT have LLM builder calls
        assert "with_generation_mode" not in script

    def test_create_generator_script_llm_mode(self):
        """
        Test generator script creation for LLM mode.

        Script should include LLM-specific builder calls.
        """
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "skills" / "create_config"))

        from skill_helpers import create_generator_script

        script = create_generator_script(
            sports=["hockey", "swimming", "volleyball"],
            mode="llm",
            provider="together",
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            retry=True,
            timestamp="20251115_130000"
        )

        # Should be valid Python
        compile(script, '<string>', 'exec')

        # LLM mode should have LLM-specific builder calls
        assert 'with_generation_mode("llm")' in script
        assert 'with_llm_provider("together")' in script
        assert 'with_llm_model("meta-llama/Llama-3.3-70B-Instruct-Turbo-Free")' in script


# ==============================================================================
# Baseline Comparison (Run BEFORE refactoring)
# ==============================================================================

"""
BASELINE TESTING PROCEDURE:

1. Run these tests WITHOUT create_config skill loaded:
   - Disable/remove .claude/skills/create_config/
   - Run manual acceptance tests
   - Document Claude's natural behavior and failure modes

2. Run these tests WITH current skill (852-line version):
   - Enable current skill
   - Run manual acceptance tests
   - Document what works and what doesn't

3. After refactoring:
   - Run tests with new refactored skill
   - Compare results
   - Ensure all scenarios pass
   - Verify no regressions

4. Success = All 3 scenarios pass with refactored skill.
"""
