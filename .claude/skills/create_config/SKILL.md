---
name: create-config
description: Create and manage configuration files for sports poetry generation with complete parameter collection
---

Create timestamped configuration files for the sports poetry multi-agent workflow using interactive conversation and pre-built utility functions.

## When to Use This Skill

Use this skill when the user:
- Asks to "create a config" or "set up configuration"
- Wants to configure sports poetry generation
- Provides a list of sports and generation preferences
- Needs help understanding configuration options

## Quick Start Example

```
User: "Create a config for basketball, soccer, and tennis"

You: I'll create a configuration for you.
     [Use skill_helpers.py utilities to create both files]

     ✓ Created output/configs/config_20251115_120000.json
     ✓ Created output/configs/generate_config_20251115_120000.py

     Ready to run: python3 orchestrator.py --config output/configs/config_20251115_120000.json
```

## Available Utilities

This skill uses pre-built functions from `skill_helpers.py`. Import and USE these directly rather than reimplementing:

```python
from skill_helpers import (
    check_api_key,           # Check env vars + .claude/claude.local.md
    create_generator_script, # Generate executable Python script
    get_setup_instructions,  # Get API key setup help
    expand_sport_category,   # Expand "winter sports" to list (optional)
    load_sport_categories    # Load categories from JSON (optional)
)
```

**Key principle:** Use these utilities to save tokens and ensure consistency. Don't reimplement their logic.

## Conversation Flow

### High-Level Steps

1. **Collect sports** (3-5 required)
   - Validate count using `config_builder.with_sports()`
   - Normalize to lowercase, check for duplicates
   - config_builder handles validation automatically

2. **Ask for generation mode** (template or llm)
   - Default: `template` (fast, no API key needed)
   - If user wants LLM: proceed to step 3
   - If template mode: skip to step 5

3. **Check API key** (LLM mode only)
   - Use `check_api_key(provider)` from skill_helpers
   - If found: proceed to step 4
   - If not found: use `get_setup_instructions(provider)` and offer to switch to template mode

4. **Confirm LLM settings** (LLM mode only)
   - Provider: "together" or "huggingface" (default: together)
   - Model: Use provider-specific defaults unless user specifies
   - Together.ai default: `meta-llama/Llama-3.3-70B-Instruct-Turbo-Free`
   - HuggingFace default: `meta-llama/Meta-Llama-3-8B-Instruct`

5. **Ask about retry behavior** (optional)
   - Default: `true` (recommended)
   - Accept: yes/no, true/false, enable/disable

6. **Show configuration summary**
   - Display all settings before creating files
   - Ask for confirmation: "Proceed? [yes/no]"

7. **Create BOTH files** (CRITICAL - see below)
   - Config JSON: `output/configs/config_{timestamp}.json`
   - Generator script: `output/configs/generate_config_{timestamp}.py`
   - Make generator script executable: `chmod +x`

## CRITICAL: Always Create Both Files

Every successful skill execution MUST create TWO files:

**File 1: Configuration JSON**
```
output/configs/config_{timestamp}.json
```
Created by: `config_builder.save(config_path)`

**File 2: Generator Script**
```
output/configs/generate_config_{timestamp}.py
```
Created by: `create_generator_script()` from skill_helpers
Made executable with: `chmod +x`

**Failure to create BOTH files is incomplete execution of this skill.**

The generator script provides:
- Reproducibility (re-run to create same config with new timestamp)
- Auditability (shows exactly how config was created)
- Self-documentation (includes all parameters in header)

## Common Usage Patterns

### Pattern 1: Template Mode (Quickest)

```python
from config_builder import ConfigBuilder
from skill_helpers import create_generator_script
from pathlib import Path
from datetime import datetime
import os, stat

# Load defaults
builder = ConfigBuilder.load_default()
builder.with_sports(["basketball", "soccer", "tennis"])

# Create config
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
config_path = Path(f"output/configs/config_{timestamp}.json")
config_path.parent.mkdir(parents=True, exist_ok=True)
builder.save(str(config_path))

# Create generator script
script = create_generator_script(
    sports=["basketball", "soccer", "tennis"],
    mode="template",
    provider="together",
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    retry=True,
    timestamp=timestamp
)

script_path = Path(f"output/configs/generate_config_{timestamp}.py")
script_path.write_text(script)
os.chmod(script_path, os.stat(script_path).st_mode | stat.S_IEXEC)

print(f"✓ Created {config_path}")
print(f"✓ Created {script_path}")
```

### Pattern 2: LLM Mode with API Key Check

```python
from skill_helpers import check_api_key, get_setup_instructions, create_generator_script
from config_builder import ConfigBuilder

# Check for API key FIRST
provider = "together"
api_key = check_api_key(provider)

if not api_key:
    # Show setup instructions
    print(get_setup_instructions(provider))
    # Offer to use template mode instead
    # Or wait for user to set key
else:
    # Proceed with LLM mode
    builder = ConfigBuilder.load_default()
    builder.with_sports(["hockey", "swimming", "volleyball"])
    builder.with_generation_mode("llm")
    builder.with_llm_provider(provider)
    builder.with_llm_model("meta-llama/Llama-3.3-70B-Instruct-Turbo-Free")

    # Save and create generator script (same as Pattern 1)
    # ...
```

## Validation & Error Handling

**config_builder.py handles all validation automatically:**

- Sports count (3-5): Error raised immediately in `with_sports()`
- Duplicates: Detected and rejected
- Empty strings: Not allowed
- Generation mode: Must be "template" or "llm"
- LLM settings: Required if mode="llm"

**You don't need to duplicate validation logic.** Just call the builder methods and let them validate.

**Error message example:**
```
ConfigValidationError: Must specify at least 3 sports (got 2)
```

These messages are already helpful - just pass them to the user.

## Troubleshooting

### Issue: "API key not found"

**Solution:**
1. Use `check_api_key(provider)` to verify
2. If not found, use `get_setup_instructions(provider)` to show user how to set it
3. Offer to switch to template mode (no API key required)

### Issue: "Only 2 sports provided"

**Solution:**
config_builder raises clear error automatically. Suggest adding one more sport:
```
You provided 2 sports, but we need 3-5.
Suggestions: tennis, volleyball, baseball
```

### Issue: "Forgot to create generator script"

**Prevention:**
Follow the CRITICAL section above. Always create BOTH files.
Use `create_generator_script()` from skill_helpers.

### Issue: "Generator script not executable"

**Solution:**
```python
import os, stat
script_path = Path(f"output/configs/generate_config_{timestamp}.py")
os.chmod(script_path, os.stat(script_path).st_mode | stat.S_IEXEC)
```

## Configuration Parameters Reference

### Required
- **sports** (list, 3-5 items): Sport names for poem generation
- **generation_mode** (string): "template" or "llm"

### Conditional (LLM mode only)
- **llm.provider** (string): "together" or "huggingface"
- **llm.model** (string): Model identifier

### Optional
- **retry_enabled** (boolean, default: true): Retry failed agents

### Auto-Generated (by orchestrator at runtime)
- **session_id**: Unique session identifier
- **timestamp**: ISO 8601 timestamp

## File Structure

```
.claude/skills/create_config/
├── SKILL.md                    # This file (~300 lines)
├── SKILL.md.old                # Backup of original (852 lines)
├── skill_helpers.py            # Pre-built utility functions
└── sport_categories.json       # Optional category mappings (if created)
```

## Testing

After using this skill, verify:

✅ Both files exist:
   - `output/configs/config_{timestamp}.json`
   - `output/configs/generate_config_{timestamp}.py`

✅ Config is valid JSON with required fields

✅ Generator script is executable:
   ```bash
   ls -l output/configs/generate_config_*.py
   # Should show -rwxr-xr-x (executable)
   ```

✅ Generator script can be run:
   ```bash
   ./output/configs/generate_config_{timestamp}.py
   # Should create new config with new timestamp
   ```

## Design Principles

This skill follows Claude Code best practices:

**Progressive Disclosure:**
- SKILL.md provides overview (~300 lines, under 500-line guideline)
- Detailed docs available separately if needed

**Utility Scripts Pattern:**
- Pre-built functions in skill_helpers.py
- Claude imports and uses them (saves tokens, ensures consistency)
- "Solve, Don't Punt" - explicit error handling in utilities

**Template Pattern:**
- `create_generator_script()` uses strict template for format-sensitive output
- Generator scripts are self-documenting and reproducible

**Evaluation-First:**
- All utilities tested with 13 automated tests (100% passing)
- Manual acceptance criteria available for full skill testing

## See Also

- **skill_helpers.py** - Utility functions (check API keys, create scripts, etc.)
- **tests/test_create_config_skill.py** - Evaluation tests and acceptance criteria
- **config_builder.py** - Python API for config creation and validation
- **config.default.json** - Default configuration template
- **README.md** - Project overview and quick start guide

## Dependencies

- `config_builder.py` - Configuration builder with validation
- `skill_helpers.py` - Utility functions for this skill
- Python 3.7+ - For f-strings and pathlib

## Version History

- **v2.0** (2025-01-15): Refactored using evaluation-first development
  - Reduced from 852 to ~300 lines
  - Added skill_helpers.py utilities
  - Progressive disclosure pattern
  - 13 automated tests (100% passing)

- **v1.0**: Original 852-line version (backed up as SKILL.md.old)
