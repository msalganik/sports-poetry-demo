"""
Utility functions for create_config skill.

Following Claude Code best practice: "Provide pre-made scripts instead of asking
Claude to generate code—more reliable, saves tokens, ensures consistency."

Claude should import and USE these functions directly rather than reimplementing
the logic. This saves tokens and ensures consistency across skill invocations.

Usage:
    from skill_helpers import check_api_key, create_generator_script

    # Check for API key
    api_key = check_api_key("together")
    if not api_key:
        print("API key not found")

    # Create generator script
    script = create_generator_script(
        sports=["basketball", "soccer", "tennis"],
        mode="template",
        provider="together",
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        retry=True,
        timestamp="20251115_120000"
    )
"""

from pathlib import Path
from typing import Optional, Dict, List
from string import Template
import json
import re
import os


def check_api_key(provider: str) -> Optional[str]:
    """
    Check for API key in environment variables and .claude/claude.local.md.

    This function implements the "Solve, Don't Punt" principle - it handles
    all API key detection logic explicitly rather than expecting Claude to
    troubleshoot.

    Args:
        provider: Either "together" or "huggingface"

    Returns:
        API key if found, None otherwise

    Example:
        >>> key = check_api_key("together")
        >>> if key:
        ...     print(f"Found key: {key[:8]}...")
        ... else:
        ...     print("No API key found")
    """
    # Determine which environment variable to check
    env_var = "TOGETHER_API_KEY" if provider == "together" else "HUGGINGFACE_API_TOKEN"

    # First, check environment variables
    api_key = os.environ.get(env_var)
    if api_key:
        return api_key

    # Second, check .claude/claude.local.md in current directory
    local_config = Path.cwd() / ".claude" / "claude.local.md"
    if local_config.exists():
        content = local_config.read_text()

        # Pattern matches various formats:
        # TOGETHER_API_KEY: value
        # TOGETHER_API_KEY = value
        # TOGETHER_API_KEY "value"
        pattern = rf'{env_var}["\s:=]+([a-zA-Z0-9_-]+)'
        match = re.search(pattern, content)

        if match:
            return match.group(1)

    # Not found in either location
    return None


def create_generator_script(
    sports: List[str],
    mode: str,
    provider: str,
    model: str,
    retry: bool,
    timestamp: str
) -> str:
    """
    Generate Python script content using the Template pattern.

    Following best practice: "Use strict templates for format-sensitive outputs."

    The generated script:
    - Is executable (caller should chmod +x)
    - Creates configs with new timestamps when run
    - Is self-documenting (includes all parameters in header)
    - Uses config_builder.py for validation

    Args:
        sports: List of 3-5 sport names
        mode: "template" or "llm"
        provider: "together" or "huggingface" (only used if mode="llm")
        model: Model name (only used if mode="llm")
        retry: Whether to enable retries
        timestamp: Timestamp string for documentation (YYYYMMDD_HHMMSS)

    Returns:
        Complete Python script as a string

    Example:
        >>> script = create_generator_script(
        ...     sports=["basketball", "soccer", "tennis"],
        ...     mode="template",
        ...     provider="together",
        ...     model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        ...     retry=True,
        ...     timestamp="20251115_120000"
        ... )
        >>> # Script can be written to file and executed
        >>> Path("config.py").write_text(script)
    """
    # Template for generator script
    # Using Template pattern from best practices for format-sensitive output
    template = Template('''#!/usr/bin/env python3
"""
Configuration Generator Script
Generated: $timestamp
Sports: $sports_display
Mode: $mode$llm_info
Retry: $retry

This script was created by the create_config skill to generate
the sports poetry configuration. It provides reproducibility and
auditability for the configuration.

You can re-run this script to regenerate the same configuration
with a new timestamp.

Usage:
    python3 $script_name
    # Or make executable and run:
    chmod +x $script_name
    ./$script_name
"""

from config_builder import ConfigBuilder
from pathlib import Path
from datetime import datetime

# Load default configuration as baseline
builder = ConfigBuilder.load_default()

# Apply sports selection
builder.with_sports($sports_repr)
$mode_config$retry_config
# Create output directory
configs_dir = Path("output/configs")
configs_dir.mkdir(parents=True, exist_ok=True)

# Generate new timestamped filename
new_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
new_config_path = configs_dir / f"config_{{new_timestamp}}.json"

# Save configuration
builder.save(str(new_config_path))

print(f"✓ Configuration saved to: {{new_config_path}}")
print(f"\\nNext step: Run the orchestrator")
print(f"  python3 orchestrator.py --config {{new_config_path}}")
''')

    # Build conditional sections based on configuration
    mode_config = ""
    if mode == "llm":
        mode_config = f'''
# Configure LLM mode
builder.with_generation_mode("llm")
builder.with_llm_provider("{provider}")
builder.with_llm_model("{model}")
'''

    retry_config = ""
    if not retry:
        retry_config = "\n# Disable retry behavior\nbuilder.with_retry(False)\n"

    # Format LLM info for header docstring
    llm_info = ""
    if mode == "llm":
        llm_info = f"\nProvider: {provider}\nModel: {model}"

    # Generate script filename for documentation
    script_name = f"generate_config_{timestamp}.py"

    # Substitute values into template
    return template.substitute(
        timestamp=timestamp,
        sports_display=", ".join(sports),
        sports_repr=repr(sports),
        mode=mode,
        llm_info=llm_info,
        retry=retry,
        mode_config=mode_config,
        retry_config=retry_config,
        script_name=script_name
    )


def get_setup_instructions(provider: str) -> str:
    """
    Get setup instructions for a specific LLM provider.

    Returns user-friendly instructions for obtaining and setting API keys.

    Args:
        provider: Either "together" or "huggingface"

    Returns:
        Formatted setup instructions

    Example:
        >>> print(get_setup_instructions("together"))
        **Setup Instructions for Together.ai**
        ...
    """
    if provider == "together":
        env_var = "TOGETHER_API_KEY"
        return f"""**Setup Instructions for Together.ai**

1. Sign up: https://together.ai/
2. Get API key: https://api.together.xyz/settings/api-keys
3. Set in terminal:
   export {env_var}="your-key-here"

   Or add to .claude/claude.local.md:
   {env_var}: your-key-here

Free tier model: meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"""

    else:  # huggingface
        env_var = "HUGGINGFACE_API_TOKEN"
        return f"""**Setup Instructions for HuggingFace**

1. Sign up: https://huggingface.co/
2. Get token: https://huggingface.co/settings/tokens
3. Set in terminal:
   export {env_var}="your-token-here"

   Or add to .claude/claude.local.md:
   {env_var}: your-token-here

Free tier model: meta-llama/Meta-Llama-3-8B-Instruct"""


# Self-test when run directly
if __name__ == "__main__":
    print("Testing skill_helpers.py utilities...")
    print()

    # Test 1: API key detection
    print("Test 1: API key detection")
    for provider in ["together", "huggingface"]:
        key = check_api_key(provider)
        if key:
            print(f"  ✓ {provider}: Found ({len(key)} chars)")
        else:
            print(f"  ✗ {provider}: Not found")
    print()

    # Test 2: Generator script creation
    print("Test 2: Generator script creation")
    script = create_generator_script(
        sports=["basketball", "soccer", "tennis"],
        mode="template",
        provider="together",
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        retry=True,
        timestamp="20251115_120000"
    )

    # Verify script is valid Python
    try:
        compile(script, '<string>', 'exec')
        print(f"  ✓ Generated valid Python script ({len(script)} chars)")
        print(f"    - Contains shebang: {script.startswith('#!/usr/bin/env python3')}")
        print(f"    - Contains ConfigBuilder: {'ConfigBuilder' in script}")
        print(f"    - Contains sports: {repr(['basketball', 'soccer', 'tennis']) in script}")
    except SyntaxError as e:
        print(f"  ✗ Invalid Python: {e}")
    print()

    # Test 3: Setup instructions
    print("Test 3: Setup instructions")
    instructions = get_setup_instructions("together")
    print(f"  ✓ Generated instructions ({len(instructions)} chars)")
    print(f"    - Contains signup URL: {'https://together.ai/' in instructions}")
    print(f"    - Contains API key URL: {'api.together.xyz' in instructions}")
    print()

    print("All tests completed!")
