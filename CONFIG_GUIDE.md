# Configuration Guide

This guide explains the two ways to create configuration files for the sports poetry demo.

## Quick Comparison

| Method | Best For | Testable | Repeatable | UX |
|--------|----------|----------|------------|-----|
| **Python API** | Scripts, CI/CD, automation | ✅ Yes | ✅ Yes | Technical |
| **Claude Skill** | Interactive, first-time users | ⚠️ Integration only | ⚠️ Conversational | Natural |

## Method 1: Python API (config_builder.py)

### When to Use
- Writing automated scripts
- CI/CD pipelines
- Jupyter notebooks
- Batch processing
- Unit testing
- When you need deterministic, repeatable behavior

### Basic Usage

```python
from config_builder import ConfigBuilder

# Create configuration
builder = ConfigBuilder()
builder.with_sports(['basketball', 'soccer', 'tennis'])
builder.with_generation_mode('template')
config_path = builder.save('config.json')
```

### Template Mode Example

```python
from config_builder import ConfigBuilder

builder = ConfigBuilder()
builder.with_sports(['basketball', 'soccer', 'tennis'])
builder.with_generation_mode('template')
builder.with_retry(True)
builder.save('config.json')
```

### LLM Mode Example

```python
from config_builder import ConfigBuilder

builder = ConfigBuilder()
builder.with_sports(['hockey', 'volleyball', 'swimming', 'baseball'])
builder.with_generation_mode('llm')
builder.with_llm_provider('together')
builder.with_llm_model('meta-llama/Llama-3.3-70B-Instruct-Turbo-Free')
builder.save('config.json')
```

### Method Chaining

```python
from config_builder import ConfigBuilder

config = (ConfigBuilder()
    .with_sports(['basketball', 'soccer', 'tennis'])
    .with_generation_mode('llm')
    .with_llm_provider('together')
    .with_retry(True)
    .save('config.json'))
```

### Loading and Modifying

```python
from config_builder import ConfigBuilder

# Load existing config
builder = ConfigBuilder.load('config.json')

# Modify and save
builder.with_generation_mode('llm')
builder.with_llm_provider('together')
builder.save('config.json')
```

### Error Handling

```python
from config_builder import ConfigBuilder, ConfigValidationError

try:
    builder = ConfigBuilder()
    builder.with_sports(['basketball'])  # Too few!
    builder.save('config.json')
except ConfigValidationError as e:
    print(f"Validation error: {e}")
    # Output: "Must specify at least 3 sports (got 1)"
```

## Method 2: Claude Skill (Interactive)

### When to Use
- First-time users
- Demos and presentations
- Exploring options
- When you prefer natural language
- Learning the system

### Usage

Simply ask Claude to create a configuration:

```
You: "Create a config for basketball, soccer, and tennis"

Claude: [Uses create_config skill]
        ✓ Created config.json with:
          - Sports: basketball, soccer, tennis
          - Mode: template
          - Retry: enabled
```

### Advanced Example

```
You: "Set up a config for winter sports using LLM mode"

Claude: **Sports Selection**
        "Winter sports" could include: hockey, skiing, snowboarding
        Please choose 3-5 from this list:

You: "hockey, skiing, snowboarding"

Claude: **LLM Provider**
        Which provider? [together/huggingface]

You: "together"

Claude: **API Key Check**
        ✓ TOGETHER_API_KEY found

        **Summary**
        📋 Sports: hockey, skiing, snowboarding
        🤖 Provider: together
        🔄 Retry: enabled

        Proceed? [yes]

You: "yes"

Claude: ✓ Created config.json
```

### Skill Features

- **Natural language parsing**: "winter sports" → [hockey, skiing, snowboarding]
- **Smart validation**: Catches errors and suggests fixes
- **Interactive clarification**: Asks questions when needed
- **API key checking**: Validates environment before proceeding
- **Summary before creation**: Shows what will be created

## Configuration Parameters Reference

### Required Parameters

| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| `sports` | list | 3-5 strings | Sport names for poem generation |
| `generation_mode` | string | "template" \| "llm" | How poems are generated |

### Conditional Parameters (LLM mode only)

| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| `llm_provider` | string | "together" \| "huggingface" | API provider |
| `llm_model` | string | Model name | Provider-specific model ID |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `retry_enabled` | boolean | true | Retry failed agents |

### Auto-Generated Parameters

| Parameter | Type | Format | Description |
|-----------|------|--------|-------------|
| `session_id` | string | `session_YYYYMMDD_HHMMSS` | Unique session identifier |
| `timestamp` | string | ISO 8601 | Creation timestamp (UTC) |

## Complete Configuration Example

```json
{
  "sports": [
    "basketball",
    "soccer",
    "tennis"
  ],
  "session_id": "session_20251101_183500",
  "timestamp": "2025-11-01T18:35:00Z",
  "retry_enabled": true,
  "generation_mode": "llm",
  "llm_provider": "together",
  "llm_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
}
```

## Validation Rules

### Sports List
- ✅ Must have 3-5 sports
- ✅ No duplicates allowed
- ✅ No empty strings
- ✅ Automatically normalized (lowercase, trimmed)

### Generation Mode
- ✅ Must be "template" or "llm"
- ✅ Case-insensitive

### LLM Configuration
- ✅ Provider must be "together" or "huggingface"
- ✅ Model can be any string (custom models allowed)
- ✅ API key must be set in environment

## Testing Your Configuration

### Python API Tests

```bash
# Run all config_builder tests
pytest tests/test_config_builder.py -v

# Run with coverage
pytest tests/test_config_builder.py --cov=config_builder --cov-report=html

# Run specific test
pytest tests/test_config_builder.py::TestConfigBuilder::test_with_sports_valid -v
```

### Integration Test

```bash
# Create config with Python API
python3 -c "
from config_builder import ConfigBuilder
builder = ConfigBuilder()
builder.with_sports(['basketball', 'soccer', 'tennis'])
builder.save('config.json')
"

# Run orchestrator
python3 orchestrator.py

# Verify output
ls output/latest/
```

## Common Patterns

### Pattern 1: Quick Template Config

```python
from config_builder import ConfigBuilder

ConfigBuilder() \
    .with_sports(['basketball', 'soccer', 'tennis']) \
    .save('config.json')
```

### Pattern 2: Full LLM Config

```python
from config_builder import ConfigBuilder

ConfigBuilder() \
    .with_sports(['hockey', 'volleyball', 'swimming', 'baseball']) \
    .with_generation_mode('llm') \
    .with_llm_provider('together') \
    .with_retry(True) \
    .save('config.json')
```

### Pattern 3: Modify Existing Config

```python
from config_builder import ConfigBuilder

builder = ConfigBuilder.load('config.json')
builder.with_sports(['swimming', 'diving', 'water polo'])
builder.save('config.json')
```

### Pattern 4: Generate Multiple Configs

```python
from config_builder import ConfigBuilder

sports_sets = [
    ['basketball', 'soccer', 'tennis'],
    ['hockey', 'volleyball', 'swimming'],
    ['baseball', 'football', 'golf', 'rugby']
]

for i, sports in enumerate(sports_sets):
    builder = ConfigBuilder()
    builder.with_sports(sports)
    builder.save(f'config_{i}.json')
```

## Troubleshooting

### Error: "Must specify at least 3 sports"

**Python API:**
```python
# ❌ Wrong
builder.with_sports(['basketball', 'soccer'])

# ✅ Correct
builder.with_sports(['basketball', 'soccer', 'tennis'])
```

**Claude Skill:**
```
You: "basketball and soccer"
Claude: You provided 2 sports, but we need 3-5.
        Would you like to add 1 more?
```

### Error: "Sports list contains duplicates"

**Python API:**
```python
# ❌ Wrong
builder.with_sports(['basketball', 'soccer', 'basketball'])

# ✅ Correct
builder.with_sports(['basketball', 'soccer', 'tennis'])
```

### Error: "Invalid generation mode"

**Python API:**
```python
# ❌ Wrong
builder.with_generation_mode('ai')

# ✅ Correct
builder.with_generation_mode('llm')
```

### Error: "LLM provider is required for LLM mode"

**Python API:**
```python
# ❌ Wrong
builder.with_generation_mode('llm')
# Missing provider!

# ✅ Correct
builder.with_generation_mode('llm')
builder.with_llm_provider('together')
builder.with_llm_model('meta-llama/Llama-3.3-70B-Instruct-Turbo-Free')
```

### Error: API key not found

**Solution:**
```bash
# For Together.ai
export TOGETHER_API_KEY="your-key-here"

# For HuggingFace
export HUGGINGFACE_API_TOKEN="your-token-here"

# Verify
echo $TOGETHER_API_KEY
```

## Best Practices

### 1. Use Template Mode for Testing

Template mode is fast and deterministic, perfect for:
- Unit tests
- CI/CD pipelines
- Development iterations
- Debugging

### 2. Use LLM Mode for Production

LLM mode generates unique, creative content:
- Final output
- Demonstrations
- Variety in results

### 3. Always Enable Retry

```python
builder.with_retry(True)  # Recommended
```

This increases success rate with minimal overhead.

### 4. Validate Before Running

```python
from config_builder import ConfigBuilder, ConfigValidationError

try:
    builder = ConfigBuilder()
    # ... configure ...
    config = builder.build()  # Validates without saving
    print("✓ Config valid")
    builder.save('config.json')
except ConfigValidationError as e:
    print(f"❌ Validation failed: {e}")
```

### 5. Version Control Your Configs

```bash
# Save to version control
git add config.json

# Or use descriptive names
config_llm_mode.json
config_template_mode.json
```

## See Also

- **API Reference**: Complete ConfigBuilder API documentation
- **README.md**: Project overview and quick start
- **CLAUDE.md**: Claude Code guidance for this repository
- **Skill Documentation**: `.claude/skills/create_config.md`
