---
name: create-config
description: Create and manage configuration files for sports poetry generation with complete parameter collection
---

Create and manage configuration files for sports poetry generation with complete parameter collection.

## Description

This skill provides an interactive interface for creating configuration files for the sports poetry multi-agent workflow. It collects all required configuration parameters through natural language conversation and uses the `config_builder.py` Python API to validate and generate timestamped configuration files in the `output/configs/` directory.

## When to Use This Skill

- User wants to create a new configuration file
- User asks to "set up configuration" or "configure the demo"
- User provides sports and generation preferences
- User needs help understanding configuration options

## Parameters Collected

### Required Parameters
1. **sports** (list of 3-5 strings) - Sport names for poem generation
2. **generation_mode** ("template" | "llm") - How poems should be generated

### Conditional Parameters (only for LLM mode)
3. **llm_provider** ("together" | "huggingface") - Which API provider to use
4. **llm_model** (string) - Model identifier for the chosen provider

### Optional Parameters (with smart defaults)
5. **retry_enabled** (boolean) - Whether to retry failed agents (default: true)

### Auto-Generated Parameters
6. **session_id** (string) - Unique identifier, auto-generated from timestamp
7. **timestamp** (string) - ISO 8601 timestamp, auto-generated

## Conversation Flow

The skill follows a structured flow to collect all necessary information:

### Step 1: Sports Selection (REQUIRED)

**Prompt:**
```
I'll help you create a sports poetry configuration.

**Sports Selection** (3-5 sports required)

Please specify which sports you'd like poems about.

You can:
• List them directly: "basketball, soccer, tennis"
• Use a category: "winter sports", "ball sports", "water sports"
• Mix approaches: "hockey and other winter sports"

What sports would you like?
```

**Validation:**
- Must have 3-5 sports
- No duplicates
- No empty strings
- Normalize to lowercase and trim whitespace

**Error Handling:**
```
If < 3 sports:
  "You provided {count} sports, but we need 3-5.
   Would you like to add {3-count} more?
   Suggestions: {suggest compatible sports}"

If > 5 sports:
  "You provided {count} sports, but the limit is 5.
   Please choose your top 5 sports from: {list}"

If duplicates found:
  "I noticed '{sport}' appears {count} times.
   Did you mean to include it once?"
```

**Category Interpretation:**
- "winter sports" → hockey, skiing, snowboarding, figure skating, curling (user picks 3-5)
- "ball sports" → basketball, soccer, tennis, volleyball, baseball (user picks 3-5)
- "water sports" → swimming, diving, water polo, surfing (user picks 3-5)
- "Olympic sports" → too broad, ask user to narrow down

### Step 2: Generation Mode (REQUIRED)

**Prompt:**
```
**Generation Mode**

How should the poems be generated?

1. **template** (recommended for testing)
   • Pre-written poems for common sports
   • Very fast (< 1 second total)
   • Works offline, no API key needed
   • Deterministic (same output every time)
   • Best for: testing, demos, quick iterations

2. **llm** (recommended for production)
   • AI-generated unique poems for each sport
   • Slower (~3-5 seconds per sport)
   • Requires API key (free tiers available)
   • Creative and varies each run
   • Best for: final output, variety, creativity

Which mode would you like? [template/llm]
Default: template
```

**Validation:**
- Must be "template" or "llm"
- Case-insensitive matching
- Handle typos: "tempate", "templates", "ai", "llms", "gpt"

**Default Behavior:**
- If user says "use defaults" or "quick": use template
- If user doesn't specify: ask explicitly

### Step 3: LLM Provider (CONDITIONAL - only if mode=llm)

**Prompt:**
```
**LLM Provider** (for AI-generated poems)

Which API provider should generate the poems?

1. **together** (recommended)
   • Together.ai API
   • Free tier: Llama-3.3-70B (high quality, no cost)
   • Fast response times
   • Setup: Sign up at https://together.ai/
   • Get API key: https://api.together.xyz/settings/api-keys

2. **huggingface**
   • HuggingFace Inference API
   • Free tier: Llama-3-8B
   • Good for experimentation
   • Setup: Sign up at https://huggingface.co/
   • Get token: https://huggingface.co/settings/tokens

Which provider? [together/huggingface]
Default: together
```

**Validation:**
- Must be "together" or "huggingface"
- Handle variations: "together.ai", "hf", "hugging face"

### Step 4: LLM Model (CONDITIONAL - only if mode=llm)

**Prompt:**
```
**LLM Model**

Which model should be used?

For Together.ai (free tier models):
• **meta-llama/Llama-3.3-70B-Instruct-Turbo-Free** (recommended)
  - Highest quality, 70B parameters
  - Best for creative poetry

• meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo-Free
  - Faster, 8B parameters
  - Good for quick iterations

• meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo-Free
  - Balanced option

For HuggingFace:
• **meta-llama/Meta-Llama-3-8B-Instruct** (recommended)

You can also specify a custom model name.

Enter model name or press Enter for default:
```

**Defaults:**
- Together.ai: `meta-llama/Llama-3.3-70B-Instruct-Turbo-Free`
- HuggingFace: `meta-llama/Meta-Llama-3-8B-Instruct`

**Validation:**
- Accept any string (custom models allowed)
- If empty/default: use provider-specific default

### Step 5: API Key Check (CONDITIONAL - only if mode=llm)

**Action:** Check if appropriate API key is set in environment

**For Together.ai:**
```python
import os
api_key = os.environ.get("TOGETHER_API_KEY")
```

**For HuggingFace:**
```python
import os
api_key = os.environ.get("HUGGINGFACE_API_TOKEN")
```

**If API key NOT found:**
```
⚠️  **API Key Required**

To use LLM mode with {provider}, you need to set an API key.

{provider_uppercase}_API_KEY environment variable not found.

**Setup Instructions:**

For Together.ai:
  1. Sign up: https://together.ai/
  2. Get API key: https://api.together.xyz/settings/api-keys
  3. Set in terminal:
     export TOGETHER_API_KEY="your-key-here"

For HuggingFace:
  1. Sign up: https://huggingface.co/
  2. Get token: https://huggingface.co/settings/tokens
  3. Set in terminal:
     export HUGGINGFACE_API_TOKEN="your-token-here"

**What would you like to do?**
1. I've set the API key - continue with LLM mode
2. Switch to template mode (no API key needed)
3. Cancel and set up API key later

Choose [1/2/3]:
```

**If API key IS found:**
```
✓ API key found for {provider}
  (Key length: {len(api_key)} characters)
```

### Step 6: Retry Behavior (OPTIONAL - always ask with default)

**Prompt:**
```
**Retry Behavior** (optional)

Should failed poetry agents be retried automatically?

• **yes** (recommended)
  - If a sport's poem generation fails, retry once
  - Increases success rate
  - Minimal additional time (~3-5 seconds per retry)

• **no**
  - If a sport fails, skip it and continue
  - Faster completion
  - May result in incomplete output

Enable automatic retry? [yes/no]
Default: yes
```

**Validation:**
- Accept: yes/no, true/false, y/n, 1/0, enable/disable
- Default to true if not specified

### Step 7: Configuration Summary

**Display before creating file:**
```
**Configuration Summary**

📋 Sports:          {sport1}, {sport2}, {sport3} ({count} sports)
⚙️  Generation:      {mode}
{if mode=llm:}
🤖 LLM Provider:    {provider}
🧠 LLM Model:       {model}
🔑 API Key:         ✓ Set ({key_length} chars)
{endif}
🔄 Retry Enabled:   {retry_enabled}
🆔 Session ID:      {session_id} (auto-generated)
⏰ Timestamp:       {timestamp} (auto-generated)

📁 Output file:     output/configs/config_{timestamp}.json
{if mode=llm:}
⏱️  Estimated time:  ~{count * 4} seconds ({count} sports × ~4s each)
💰 API cost:        Free (using free tier model)
{else:}
⏱️  Estimated time:  < 1 second
{endif}

Proceed with this configuration? [yes/no/edit]
```

**Actions:**
- `yes`: Create configuration file
- `no`: Cancel
- `edit`: Ask which parameter to change and restart from that step

### Step 8: File Creation

**Using config_builder.py:**
```python
from config_builder import ConfigBuilder, ConfigValidationError
from pathlib import Path
from datetime import datetime

try:
    # Always start from default config
    builder = ConfigBuilder.load_default()

    # Apply user-specified changes
    builder.with_sports(sports_list)

    if mode != "template":  # Only change if different from default
        builder.with_generation_mode(mode)

    if mode == "llm":
        if provider != "together":  # Only change if different from default
            builder.with_llm_provider(provider)
        if model != "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free":  # Only change if different
            builder.with_llm_model(model)

    if not retry_enabled:  # Only change if different from default (true)
        builder.with_retry(retry_enabled)

    # Create output/configs directory if it doesn't exist
    configs_dir = Path("output/configs")
    configs_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    config_filename = f"config_{timestamp}.json"
    config_path = configs_dir / config_filename

    # Save configuration to output/configs directory
    builder.save(str(config_path))

    print(f"✓ Successfully created {config_path}")
    print(f"\nNext step: Run the orchestrator with this config")
    print(f"  cd sports_poetry_demo")
    print(f"  python3 orchestrator.py --config {config_path}")

except FileNotFoundError as e:
    print(f"❌ Error: {e}")
    print(f"The config.default.json file is missing from the repository.")
except ConfigValidationError as e:
    print(f"❌ Configuration error: {e}")
    print(f"Please try again or check your inputs.")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    print(f"Please report this issue.")
```

## Usage Examples

### Example 1: Quick Start (Minimal Input)

```
User: "Create a config for basketball, soccer, and tennis"

Skill: Great! I'll create a configuration starting from defaults:

       Default settings:
       • Sports: basketball, soccer, tennis (will use default)
       • Mode: template (default)
       • Retry: enabled (default)

       You're using the default sports. Keep all defaults? [yes/no]

User: "yes"

Skill: ✓ Created output/configs/config_20251101_184500.json

       Next step: python3 orchestrator.py --config output/configs/config_20251101_184500.json
```

### Example 2: LLM Mode (Full Flow)

```
User: "Set up a config using LLM mode"

Skill: **Sports Selection**
       Which sports? (3-5 sports)

User: "winter sports"

Skill: "Winter sports" could include: hockey, skiing, snowboarding,
       figure skating, curling

       Please choose 3-5 from this list:

User: "hockey, skiing, snowboarding"

Skill: ✓ 3 sports selected

       **Generation Mode**
       You specified LLM mode.

       **LLM Provider**
       Which provider? [together/huggingface]

User: "together"

Skill: **LLM Model**
       Using default: meta-llama/Llama-3.3-70B-Instruct-Turbo-Free
       Change? [yes/no]

User: "no"

Skill: **API Key Check**
       ✓ TOGETHER_API_KEY found (64 chars)

       **Retry Behavior**
       Enable retry? [yes/no] (default: yes)

User: "yes"

Skill: **Summary**
       📋 Sports: hockey, skiing, snowboarding
       🤖 Provider: together
       🧠 Model: Llama-3.3-70B-Instruct-Turbo-Free
       🔄 Retry: enabled

       Proceed? [yes/no]

User: "yes"

Skill: ✓ Created output/configs/config_20251101_184500.json
```

### Example 3: Error Recovery

```
User: "Create config for basketball, soccer"

Skill: ❌ Error: Only 2 sports provided (need 3-5)

       You entered: basketball, soccer

       Suggestions to add:
       • tennis (complements ball sports)
       • volleyball (another ball sport)
       • baseball (similar skill set)

       Please add 1 more sport:

User: "tennis"

Skill: ✓ Updated to: basketball, soccer, tennis

       [Continues with generation mode question...]
```

### Example 4: API Key Missing

```
User: "Create config with swimming, hockey, volleyball using LLM"

Skill: **LLM Provider**
       [together selected]

       **API Key Check**
       ❌ TOGETHER_API_KEY not found

       Setup instructions:
       1. https://together.ai/ → Sign up
       2. Get key: https://api.together.xyz/settings/api-keys
       3. export TOGETHER_API_KEY="your-key"

       Options:
       1. I've set it - continue
       2. Use template mode instead
       3. Cancel

User: "2"

Skill: Switching to template mode...

       **Summary**
       📋 Sports: swimming, hockey, volleyball
       ⚙️  Mode: template
       🔄 Retry: enabled

       Proceed? [yes]

User: "yes"

Skill: ✓ Created output/configs/config_20251101_184500.json with template mode
```

## Error Handling

### Sports Validation Errors

**Too few sports:**
```
❌ Error: Need 3-5 sports (you provided {count})
   Current: {list}
   Please add {needed} more sport(s)
```

**Too many sports:**
```
❌ Error: Maximum 5 sports (you provided {count})
   Current: {list}
   Please choose your top 5
```

**Duplicates:**
```
❌ Error: Duplicate sport found
   '{sport}' appears {count} times
   Please provide unique sports
```

**Empty/Invalid:**
```
❌ Error: Invalid sport name detected
   All sports must be non-empty strings
   Please check your input
```

### Generation Mode Errors

**Invalid mode:**
```
❌ Error: Invalid mode '{input}'
   Valid options: 'template' or 'llm'
   Did you mean 'llm'? [yes/no]
```

### LLM Configuration Errors

**Invalid provider:**
```
❌ Error: Invalid provider '{input}'
   Valid options: 'together' or 'huggingface'
   Would you like to use 'together' (recommended)? [yes/no]
```

**Missing API key:**
```
❌ Error: API key required for LLM mode
   {PROVIDER}_API_KEY not set
   See setup instructions above
```

### File Creation Errors

**Permission denied:**
```
❌ Error: Cannot write to output/configs/
   Permission denied
   Check directory permissions or try a different location
```

**File exists:**
```
Note: Each config is saved with a unique timestamp, so conflicts are rare.
If a config file already exists at the exact same second, a random suffix will be added.
```

## Sport Category Mappings

### Predefined Categories

**Winter Sports:**
- hockey
- skiing
- snowboarding
- figure skating
- curling
- ice skating
- bobsled

**Ball Sports:**
- basketball
- soccer
- tennis
- volleyball
- baseball
- football
- golf
- rugby

**Water Sports:**
- swimming
- diving
- water polo
- surfing
- rowing
- sailing

**Track & Field:**
- running
- sprinting
- marathon
- hurdles
- long jump
- high jump
- javelin

**Combat Sports:**
- boxing
- wrestling
- judo
- karate
- taekwondo
- fencing

**Racquet Sports:**
- tennis
- badminton
- squash
- table tennis

**Team Sports:**
- basketball
- soccer
- volleyball
- football
- hockey
- baseball
- rugby

**Individual Sports:**
- tennis
- golf
- swimming
- gymnastics
- track and field

## Dependencies

This skill requires:
- `config_builder.py` - Python API for config generation and validation
- Python 3.7+ (for the config_builder module)

## Notes

- Config files are saved to `output/configs/config_{timestamp}.json`
- Timestamp format: `YYYYMMDD_HHMMSS`
- Each config gets a unique timestamped filename to prevent overwrites
- API keys are validated but never displayed or logged
- The orchestrator must be run with `--config` flag pointing to the created file
- All user inputs are normalized (lowercase, trimmed) for consistency
