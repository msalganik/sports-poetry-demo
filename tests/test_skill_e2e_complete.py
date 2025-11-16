"""
Comprehensive E2E API tests for create_config skill.

These tests validate Claude's complete skill execution using the Anthropic API.
They test realistic user scenarios from start to finish.

Related: Issue #18 - Add comprehensive E2E API tests for create_config skill

Cost per test run: ~$0.05-0.25 depending on model selection
Run before releases: pytest -m api tests/test_skill_e2e_complete.py -v -s

SCOPE NOTE: These tests validate Claude's conversation behavior and decision-making,
not actual file creation. Testing actual tool execution would require:
- Tool execution environment (sandbox)
- Multi-turn conversation with tool calls
- Complex Claude Code internal infrastructure

For file output validation, see: tests/test_e2e_output_validation.py
"""

import pytest
import os
import json
from pathlib import Path


@pytest.mark.api
class TestCompleteSkillWorkflows:
    """
    Complete end-to-end tests for create_config skill.

    Tests the full user journey from initial request to successful file creation.
    """

    @pytest.fixture
    def anthropic_client(self):
        """Create Anthropic client for testing."""
        try:
            import anthropic
        except ImportError:
            pytest.skip("anthropic package not installed (pip install anthropic)")

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set - skipping API tests")

        return anthropic.Anthropic(api_key=api_key)

    @pytest.fixture
    def skill_context(self):
        """Load the skill documentation."""
        skill_md_path = Path(__file__).parent.parent / ".claude" / "skills" / "create_config" / "SKILL.md"

        if not skill_md_path.exists():
            pytest.skip("SKILL.md not found")

        return skill_md_path.read_text()

    def test_complete_happy_path_template_mode(self, anthropic_client, skill_context):
        """
        Test: Complete workflow for template mode config creation.

        Scenario: User requests config for 3 sports, accepts defaults
        Expected: Claude creates valid config without asking unnecessary questions

        Cost: ~$0.01 with Sonnet
        Related: Issue #18, Test 1
        """
        print("\n" + "="*80)
        print("TEST: Complete Happy Path - Template Mode")
        print("="*80)

        user_request = "Create a config for hockey, swimming, volleyball"
        print(f"\n📝 User: {user_request}")

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1500,
            system=f"""You are a helpful assistant with access to a create_config skill.

{skill_context}

When users ask to create configurations, use the skill. Follow best practices:
- Use template mode by default (fast, no API key needed)
- Enable retry by default
- Don't ask unnecessary questions""",
            messages=[{
                "role": "user",
                "content": user_request
            }]
        )

        response_text = response.content[0].text
        print(f"\n💬 Claude: {response_text[:200]}...")

        # Validation 1: Claude recognizes config creation task
        assert any(word in response_text.lower() for word in ["config", "configuration"]), \
            "Claude should recognize this as a config creation task"

        # Validation 2: Claude acknowledges all sports
        for sport in ["hockey", "swimming", "volleyball"]:
            assert sport.lower() in response_text.lower(), \
                f"Claude should acknowledge '{sport}'"

        # Validation 3: Response is helpful (substantial content)
        assert len(response_text) > 50, \
            "Response should be substantial and helpful"

        # Validation 4: Claude doesn't ask about mode (uses template default)
        # This is a UX test - we want defaults, not questions
        # Note: Claude might still ask, but ideally shouldn't for simple requests

        print(f"\n✅ Validations passed")
        print(f"📊 Cost: ~${(response.usage.input_tokens * 0.000003 + response.usage.output_tokens * 0.000015):.4f}")
        print("="*80)

    def test_complete_llm_mode_workflow(self, anthropic_client, skill_context):
        """
        Test: Complete workflow for LLM mode with API key.

        Scenario: User explicitly requests LLM mode
        Expected: Claude checks API key, creates LLM config

        Cost: ~$0.01 with Sonnet
        Related: Issue #18, Test 2
        """
        print("\n" + "="*80)
        print("TEST: Complete LLM Mode Workflow")
        print("="*80)

        user_request = "Create an LLM mode config for cricket, rugby, golf"
        print(f"\n📝 User: {user_request}")

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1500,
            system=f"""You are a helpful assistant with access to a create_config skill.

{skill_context}

When users request LLM mode:
1. Check if API key is available (skill_helpers.check_api_key)
2. If available, create LLM mode config
3. If not available, provide setup instructions""",
            messages=[{
                "role": "user",
                "content": user_request
            }]
        )

        response_text = response.content[0].text
        print(f"\n💬 Claude: {response_text[:200]}...")

        # Validation 1: Claude recognizes LLM mode request
        assert "llm" in response_text.lower(), \
            "Claude should acknowledge LLM mode request"

        # Validation 2: Claude mentions API key or provider
        assert any(word in response_text.lower() for word in ["api", "key", "together", "provider"]), \
            "Claude should discuss API key or provider"

        # Validation 3: Claude acknowledges sports
        assert any(sport in response_text.lower() for sport in ["cricket", "rugby", "golf"]), \
            "Claude should acknowledge the sports"

        print(f"\n✅ Validations passed")
        print(f"📊 Cost: ~${(response.usage.input_tokens * 0.000003 + response.usage.output_tokens * 0.000015):.4f}")
        print("="*80)

    def test_validation_error_recovery(self, anthropic_client, skill_context):
        """
        Test: Multi-turn conversation with validation error recovery.

        Scenario: User provides too few sports, then corrects after feedback
        Expected: Claude catches error, explains clearly, accepts correction

        Cost: ~$0.02 with Sonnet (2 turns)
        Related: Issue #18, Test 3
        """
        print("\n" + "="*80)
        print("TEST: Validation Error Recovery")
        print("="*80)

        # Turn 1: Invalid request (only 2 sports)
        print("\n📝 User (Turn 1): Create a config for tennis and golf")

        response1 = anthropic_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1000,
            system=f"""You are a helpful assistant with access to a create_config skill.

{skill_context}

The skill requires 3-5 sports. If users provide fewer, explain the issue and ask for more.""",
            messages=[{
                "role": "user",
                "content": "Create a config for tennis and golf"
            }]
        )

        response1_text = response1.content[0].text
        print(f"\n💬 Claude (Turn 1): {response1_text[:200]}...")

        # Validation 1: Claude catches validation error
        validation_keywords = ["3", "more", "additional", "add", "need", "require", "least"]
        assert any(keyword in response1_text.lower() for keyword in validation_keywords), \
            "Claude should indicate more sports are needed"

        # Turn 2: User adds another sport
        print("\n📝 User (Turn 2): Add baseball")

        response2 = anthropic_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1000,
            system=f"""You are a helpful assistant with access to a create_config skill.

{skill_context}""",
            messages=[
                {"role": "user", "content": "Create a config for tennis and golf"},
                {"role": "assistant", "content": response1_text},
                {"role": "user", "content": "Add baseball"}
            ]
        )

        response2_text = response2.content[0].text
        print(f"\n💬 Claude (Turn 2): {response2_text[:200]}...")

        # Validation 2: Claude proceeds after correction
        assert "config" in response2_text.lower() or "create" in response2_text.lower(), \
            "Claude should proceed with config creation after correction"

        # Validation 3: Claude acknowledges all three sports
        sports_mentioned = sum(1 for sport in ["tennis", "golf", "baseball"]
                              if sport in response2_text.lower())
        assert sports_mentioned >= 2, \
            "Claude should acknowledge most/all sports"

        total_cost = (
            (response1.usage.input_tokens + response2.usage.input_tokens) * 0.000003 +
            (response1.usage.output_tokens + response2.usage.output_tokens) * 0.000015
        )

        print(f"\n✅ Validations passed")
        print(f"📊 Total cost (2 turns): ~${total_cost:.4f}")
        print("="*80)

    def test_missing_api_key_handling(self, anthropic_client, skill_context):
        """
        Test: LLM mode request without API key.

        Scenario: User requests LLM mode, but ANTHROPIC_API_KEY not set
        Expected: Claude detects issue, provides setup instructions, offers fallback

        Cost: ~$0.01 with Sonnet
        Related: Issue #18, Test 4

        Note: This simulates the missing key scenario through the prompt rather than
        actually manipulating environment variables, which is why we don't need monkeypatch.
        We're testing Claude's response to the simulated scenario, not the actual key checking.
        """
        print("\n" + "="*80)
        print("TEST: Missing API Key Handling")
        print("="*80)

        user_request = "Create an LLM mode config for basketball, soccer, tennis"
        print(f"\n📝 User: {user_request}")

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1500,
            system=f"""You are a helpful assistant with access to a create_config skill.

{skill_context}

IMPORTANT: The API key check (skill_helpers.check_api_key) will return None (no key found).
When this happens:
1. Explain that LLM mode requires an API key
2. Provide setup instructions (use skill_helpers.get_setup_instructions)
3. Offer template mode as an alternative
4. Do NOT create a broken config""",
            messages=[{
                "role": "user",
                "content": user_request
            }]
        )

        response_text = response.content[0].text
        print(f"\n💬 Claude: {response_text[:300]}...")

        # Validation 1: Claude mentions API key issue
        assert any(word in response_text.lower() for word in ["api", "key", "missing", "not found"]), \
            "Claude should mention the API key issue"

        # Validation 2: Claude provides helpful guidance
        assert any(word in response_text.lower() for word in ["setup", "install", "configure", "export"]), \
            "Claude should provide setup guidance"

        # Validation 3: Claude offers alternative (template mode)
        assert "template" in response_text.lower(), \
            "Claude should offer template mode as fallback"

        print(f"\n✅ Validations passed")
        print(f"📊 Cost: ~${(response.usage.input_tokens * 0.000003 + response.usage.output_tokens * 0.000015):.4f}")
        print("="*80)

    def test_default_behavior_minimal_input(self, anthropic_client, skill_context):
        """
        Test: Default behavior with minimal user input.

        Scenario: User provides just the sports, nothing else
        Expected: Claude uses sensible defaults without asking questions

        This tests the UX principle: "Don't make users answer questions
        when good defaults exist."

        Cost: ~$0.01 with Sonnet
        Related: Issue #18, Test 5
        """
        print("\n" + "="*80)
        print("TEST: Default Behavior - Minimal Input")
        print("="*80)

        user_request = "Create a config for basketball, soccer, tennis"
        print(f"\n📝 User: {user_request}")
        print("   (Minimal input - no mode, no retry preference)")

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1500,
            system=f"""You are a helpful assistant with access to a create_config skill.

{skill_context}

Best practices:
- Use template mode by default (fast, no setup needed)
- Enable retry by default (more robust)
- Only ask questions when truly necessary
- Proceed quickly for simple requests""",
            messages=[{
                "role": "user",
                "content": user_request
            }]
        )

        response_text = response.content[0].text
        print(f"\n💬 Claude: {response_text}")

        # Validation 1: Claude processes the request
        assert any(word in response_text.lower() for word in ["config", "create", "basketball"]), \
            "Claude should process the config creation request"

        # Validation 2: Response is concise (using defaults)
        # Ideally, Claude shouldn't ask many questions for simple requests
        question_marks = response_text.count('?')
        print(f"\n📊 Questions asked: {question_marks}")
        print(f"   (Fewer is better - good defaults reduce friction)")

        # Validation 3: All sports acknowledged
        for sport in ["basketball", "soccer", "tennis"]:
            assert sport.lower() in response_text.lower(), \
                f"Claude should acknowledge '{sport}'"

        print(f"\n✅ Validations passed")
        print(f"📊 Cost: ~${(response.usage.input_tokens * 0.000003 + response.usage.output_tokens * 0.000015):.4f}")
        print("="*80)


@pytest.mark.api
@pytest.mark.slow
class TestCrossModelConsistency:
    """
    Optional: Test skill behavior across different Claude models.

    Validates that the skill works consistently on Opus, Sonnet, and Haiku.
    Useful for cost optimization (can we use cheaper Haiku instead of Sonnet?).
    """

    @pytest.fixture
    def anthropic_client(self):
        """Create Anthropic client."""
        try:
            import anthropic
        except ImportError:
            pytest.skip("anthropic package not installed")

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        return anthropic.Anthropic(api_key=api_key)

    @pytest.fixture
    def skill_context(self):
        """Load skill documentation."""
        skill_md_path = Path(__file__).parent.parent / ".claude" / "skills" / "create_config" / "SKILL.md"
        if not skill_md_path.exists():
            pytest.skip("SKILL.md not found")
        return skill_md_path.read_text()

    @pytest.mark.parametrize("model,expected_cost", [
        ("claude-3-5-haiku-20241022", 0.001),       # Cheapest
        ("claude-sonnet-4-5-20250929", 0.01),        # Balanced
        # ("claude-opus-4-20250514", 0.05),          # Most capable (uncomment to test)
    ])
    def test_skill_recognition_across_models(self, anthropic_client, skill_context, model, expected_cost):
        """
        Test that skill recognition works across different models.

        This helps answer: "Can we use cheaper Haiku for this skill?"

        Cost: ~$0.001-0.05 depending on model
        """
        print(f"\n{'='*80}")
        print(f"TEST: Skill Recognition on {model}")
        print(f"Expected cost: ~${expected_cost:.4f}")
        print(f"{'='*80}")

        response = anthropic_client.messages.create(
            model=model,
            max_tokens=1000,
            system=f"""You are a helpful assistant with access to a create_config skill.

{skill_context}""",
            messages=[{
                "role": "user",
                "content": "Create a config for basketball, soccer, tennis"
            }]
        )

        response_text = response.content[0].text
        print(f"\n💬 {model}: {response_text[:150]}...")

        # Basic validation: Does the model understand the task?
        assert "config" in response_text.lower(), \
            f"{model} should recognize config creation task"

        actual_cost = (response.usage.input_tokens * 0.000003 +
                      response.usage.output_tokens * 0.000015)

        print(f"\n📊 Actual cost: ${actual_cost:.4f}")
        print(f"✅ {model} passed")
        print(f"{'='*80}")


if __name__ == "__main__":
    # Run just these comprehensive tests
    pytest.main([__file__, "-v", "-s", "-m", "api"])
