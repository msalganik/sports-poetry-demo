"""
Demonstration API test with detailed output.

This is a learning example that shows what you can test with the Anthropic API.
"""

import pytest
import os
from pathlib import Path


@pytest.mark.api
class TestClaudeSkillRecognitionDemo:
    """Demo test showing Claude's actual responses."""

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
        """Load the skill documentation."""
        skill_md_path = Path(__file__).parent.parent / ".claude" / "skills" / "create_config" / "SKILL.md"
        if not skill_md_path.exists():
            pytest.skip("SKILL.md not found")
        return skill_md_path.read_text()

    def test_claude_recognizes_config_creation(self, anthropic_client, skill_context):
        """
        Test: Does Claude recognize when to create a config?

        User says: "Create a config for basketball, soccer, and tennis"

        We want to verify:
        1. Claude understands this is a config creation task
        2. Claude mentions the sports provided
        3. Claude responds helpfully

        This helps validate that our skill description (SKILL.md) is clear.
        """
        print("\n" + "="*80)
        print("TEST: Claude Skill Recognition")
        print("="*80)
        print("\n📝 User input:")
        print('   "Create a config for basketball, soccer, and tennis"')
        print("\n🤖 Calling Claude API (this costs ~$0.01)...")

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

        response_text = response.content[0].text

        print("\n💬 Claude's response:")
        print("   " + "-"*76)
        for line in response_text.split('\n'):
            print(f"   {line}")
        print("   " + "-"*76)

        print("\n📊 Token usage:")
        print(f"   Input:  {response.usage.input_tokens} tokens")
        print(f"   Output: {response.usage.output_tokens} tokens")
        print(f"   Total:  {response.usage.input_tokens + response.usage.output_tokens} tokens")
        print(f"   Cost:   ~${(response.usage.input_tokens * 0.000003 + response.usage.output_tokens * 0.000015):.4f}")

        # Validation
        response_lower = response_text.lower()

        print("\n✅ Validating response:")

        # Test 1: Does Claude mention "config" or "configuration"?
        has_config = any(word in response_lower for word in ["config", "configuration"])
        print(f"   {'✓' if has_config else '✗'} Mentions 'config' or 'configuration': {has_config}")

        # Test 2: Does Claude mention the sports?
        has_sports = any(sport in response_lower for sport in ["basketball", "soccer", "tennis"])
        print(f"   {'✓' if has_sports else '✗'} Acknowledges sports: {has_sports}")

        # Test 3: Is response helpful? (not too short)
        is_helpful = len(response_text) > 50
        print(f"   {'✓' if is_helpful else '✗'} Response is substantial (>50 chars): {is_helpful}")

        print("\n" + "="*80)
        print("INSIGHTS FROM THIS TEST:")
        print("="*80)
        print("1. We can verify Claude understands the skill's purpose")
        print("2. We can see exactly what Claude would say to users")
        print("3. We can validate the skill description is clear")
        print("4. We can test across different models (Opus, Sonnet, Haiku)")
        print("="*80)

        # Assert validations
        assert has_config, "Claude should recognize this as a config creation task"
        assert has_sports, "Claude should acknowledge the sports provided"

    def test_claude_validates_input(self, anthropic_client, skill_context):
        """
        Test: Does Claude catch invalid input?

        User says: "Create a config for basketball and soccer"
        (Only 2 sports, but we need 3-5)

        We want to verify Claude catches this validation error.
        """
        print("\n" + "="*80)
        print("TEST: Claude Input Validation")
        print("="*80)
        print("\n📝 User input:")
        print('   "Create a config for basketball and soccer"')
        print('   (Only 2 sports - should trigger validation!)')
        print("\n🤖 Calling Claude API...")

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

        response_text = response.content[0].text

        print("\n💬 Claude's response:")
        print("   " + "-"*76)
        for line in response_text.split('\n'):
            print(f"   {line}")
        print("   " + "-"*76)

        print("\n📊 Token usage:")
        print(f"   Cost: ~${(response.usage.input_tokens * 0.000003 + response.usage.output_tokens * 0.000015):.4f}")

        # Validation
        response_lower = response_text.lower()

        print("\n✅ Validating response:")

        # Does Claude mention needing more sports or the number 3?
        validation_keywords = ["3", "more", "additional", "add", "need", "require"]
        catches_error = any(keyword in response_lower for keyword in validation_keywords)

        print(f"   {'✓' if catches_error else '✗'} Catches validation issue: {catches_error}")

        print("\n" + "="*80)
        print("INSIGHT: Claude can validate input BEFORE creating files!")
        print("="*80)

        assert catches_error, "Claude should ask for more sports"


if __name__ == "__main__":
    # Run this test file
    pytest.main([__file__, "-v", "-s", "-m", "api"])
