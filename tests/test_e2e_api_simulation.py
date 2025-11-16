"""
End-to-End API Simulation Tests

Approach 2: Test Claude's actual decision-making using the Anthropic API.

This approach:
- Uses the real Claude API to process user inputs
- Tests Claude's ability to recognize when to use the skill
- Validates Claude's decision-making and conversation flow
- Can test different models (Opus, Sonnet, Haiku)

Use when: You need to test AI decision-making and skill recognition
Don't use when: You just need to validate outputs (use Approach 1 instead)

IMPORTANT: These tests require an ANTHROPIC_API_KEY and will cost money to run.
They are marked with @pytest.mark.api so you can skip them:
    pytest -m "not api"  # Skip API tests
    pytest -m api        # Run only API tests
"""

import pytest
import json
import os
from pathlib import Path

# Mark all tests in this file as requiring API access
pytestmark = pytest.mark.api


class TestClaudeSkillRecognition:
    """
    Test Claude's ability to recognize when to use the create_config skill.

    These tests validate that Claude understands the skill's purpose and
    invokes it appropriately.
    """

    @pytest.fixture
    def anthropic_client(self):
        """
        Create Anthropic client for testing.

        Requires ANTHROPIC_API_KEY environment variable.
        """
        try:
            import anthropic
        except ImportError:
            pytest.skip("anthropic package not installed (pip install anthropic)")

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set (these tests cost money)")

        return anthropic.Anthropic(api_key=api_key)

    @pytest.fixture
    def skill_context(self):
        """
        Load the skill documentation to provide to Claude.

        This simulates what Claude Code does - it includes SKILL.md in the context.
        """
        skill_md_path = Path(__file__).parent.parent / ".claude" / "skills" / "create_config" / "SKILL.md"

        if not skill_md_path.exists():
            pytest.skip("SKILL.md not found")

        return skill_md_path.read_text()

    def test_claude_recognizes_skill_trigger(self, anthropic_client, skill_context):
        """
        Test that Claude recognizes when to use the create_config skill.

        User input: "Create a config for basketball, soccer, and tennis"
        Expected: Claude should mention using the create_config skill
        """
        # This is a simplified test that checks if Claude mentions the skill
        # A full implementation would need to handle tool execution

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1000,
            system=f"""You are a helpful assistant with access to a create_config skill.

{skill_context}

When users ask to create configurations, you should use the create_config skill.""",
            messages=[{
                "role": "user",
                "content": "Create a config for basketball, soccer, and tennis"
            }]
        )

        response_text = response.content[0].text.lower()

        # Claude should recognize this as a config creation task
        # It might mention: "config", "create", "skill", "basketball", etc.
        assert any(word in response_text for word in ["config", "configuration", "create"]), \
            f"Claude should recognize config creation task. Response: {response_text}"

        assert any(sport in response_text for sport in ["basketball", "soccer", "tennis"]), \
            f"Claude should acknowledge the sports. Response: {response_text}"

    def test_claude_validates_sports_count(self, anthropic_client, skill_context):
        """
        Test that Claude validates sports count (3-5 required).

        User input: "Create a config for basketball and soccer"  # Only 2 sports
        Expected: Claude should ask for more sports
        """
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1000,
            system=f"""You are a helpful assistant with access to a create_config skill.

{skill_context}

The skill requires 3-5 sports. If users provide fewer, ask them to add more.""",
            messages=[{
                "role": "user",
                "content": "Create a config for basketball and soccer"
            }]
        )

        response_text = response.content[0].text.lower()

        # Claude should recognize the validation issue
        # Look for indications that more sports are needed
        validation_keywords = ["3", "more", "additional", "add", "need", "require"]

        assert any(keyword in response_text for keyword in validation_keywords), \
            f"Claude should ask for more sports. Response: {response_text}"


class TestClaudeConversationFlow:
    """
    Test Claude's conversation flow when using the skill.

    These tests verify that Claude:
    1. Asks appropriate questions
    2. Provides helpful responses
    3. Handles errors gracefully
    """

    @pytest.fixture
    def anthropic_client(self):
        try:
            import anthropic
        except ImportError:
            pytest.skip("anthropic package not installed")

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        return anthropic.Anthropic(api_key=api_key)

    def test_claude_handles_llm_mode_without_api_key(self, anthropic_client):
        """
        Test that Claude handles LLM mode request when API key is missing.

        Expected: Claude should either:
        1. Check for API key and provide setup instructions if missing
        2. Offer to use template mode instead
        """
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1000,
            system="""You are a helpful assistant helping users create configurations.

When users request LLM mode, you should check if they have an API key configured.
If not, provide setup instructions or offer template mode as an alternative.""",
            messages=[{
                "role": "user",
                "content": "Create an LLM mode config for hockey, swimming, volleyball"
            }]
        )

        response_text = response.content[0].text.lower()

        # Claude should mention LLM or API key or offer alternatives
        llm_keywords = ["llm", "api", "key", "template", "mode"]

        assert any(keyword in response_text for keyword in llm_keywords), \
            f"Claude should discuss LLM mode. Response: {response_text}"


@pytest.mark.skip(reason="Example of full tool execution test - requires complex setup")
class TestClaudeToolExecution:
    """
    Advanced: Test Claude's actual tool execution.

    This requires:
    1. Implementing a tool execution environment
    2. Providing Claude with actual tool access
    3. Validating file creation and outputs

    This is similar to what Claude Code does internally.

    For learning: This shows the concept but is complex to implement.
    In practice, you'd use Claude Code's own testing framework.
    """

    def test_claude_executes_skill_end_to_end(self):
        """
        Full end-to-end test with tool execution.

        This would:
        1. Send user message to Claude
        2. Let Claude call tools (skill_helpers functions)
        3. Execute tool calls in a sandbox
        4. Return results to Claude
        5. Validate final outputs

        Implementation complexity:
        - Tool execution sandbox
        - Multi-turn conversation handling
        - File system isolation
        - Error handling
        """
        pass  # Placeholder for advanced implementation


# Utility for debugging API tests
def print_api_usage(response):
    """Helper to print API usage info."""
    usage = response.usage
    print(f"\nAPI Usage:")
    print(f"  Input tokens: {usage.input_tokens}")
    print(f"  Output tokens: {usage.output_tokens}")
    print(f"  Total tokens: {usage.input_tokens + usage.output_tokens}")


if __name__ == "__main__":
    # Run API tests with verbose output
    pytest.main([__file__, "-v", "-m", "api", "-s"])
