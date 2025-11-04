# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Sports Poetry Multi-Agent Workflow Demo** that showcases multi-agent coordination with parallel execution, provenance logging, and result synthesis.

**Workflow**: User provides sports list → Claude validates and creates timestamped config file → Orchestrator launches parallel poetry agents → Each agent generates haiku + sonnet → Analyzer synthesizes results → Full audit logs created

## Common Commands

### Running the Demo

```bash
cd sports_poetry_demo
python3 orchestrator.py --config output/configs/config_TIMESTAMP.json
```

Requires a valid config file. Claude Code typically creates timestamped config files in `output/configs/` interactively based on user input. The orchestrator can also use a default config path if `--config` is not specified.

### Testing

```bash
cd sports_poetry_demo
pytest                           # Run all tests
pytest -v                        # Verbose output
pytest tests/test_poetry_agent.py  # Run specific test file
pytest -k "test_name"            # Run tests matching pattern
```

### Development Dependencies

```bash
cd sports_poetry_demo
pip install -r requirements.txt      # Install LLM dependencies (optional)
pip install -r requirements-dev.txt  # Install testing dependencies
```

## Architecture

### Multi-Agent Orchestration Pattern

- **orchestrator.py** - Main coordinator that launches agents in parallel using ThreadPoolExecutor
- **poetry_agent.py** - Individual agent (subprocess) that generates poems for one sport
- **analyzer_agent.py** - Synthesis agent that compares all results and creates final report

### Key Design Patterns

1. **Parallel Execution**: Agents run simultaneously via `concurrent.futures.ThreadPoolExecutor` (orchestrator.py:267)
2. **Graceful Degradation**: Failed agents don't stop the workflow; orchestrator continues with successful ones
3. **Session Isolation**: Each run creates a unique session directory under `output/{session_id}/`
4. **Provenance Logging**: Every action logged to `execution_log.jsonl` with timestamps via ProvenanceLogger class

### Configuration System

The `config.json` structure (template mode):
```json
{
  "sports": ["basketball", "soccer", "tennis"],
  "retry_enabled": true,
  "generation_mode": "template"
}
```

The `config.json` structure (LLM mode):
```json
{
  "sports": ["basketball", "soccer", "tennis"],
  "retry_enabled": true,
  "generation_mode": "llm",
  "llm": {
    "provider": "together",
    "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
  }
}
```

**Important Notes**:
- `session_id` is **generated at runtime** by the orchestrator, not stored in config
- LLM settings are **only included when using LLM mode**
- The `llm` object is auto-populated with defaults when switching to LLM mode

**Generation Modes**:
- `template` (default): Fast, deterministic, uses pre-written templates
- `llm`: Calls Together.ai or HuggingFace API for unique poems (requires API key)

### Directory Structure

```
sports_poetry_demo/
├── orchestrator.py          # Main workflow coordinator
├── poetry_agent.py          # Individual poetry generator
├── analyzer_agent.py        # Result synthesis
├── config_builder.py        # Configuration builder with validation
├── config.default.json      # Default configuration template (in git)
├── output/
│   ├── configs/            # Timestamped input configs created by skill
│   │   └── config_TIMESTAMP.json
│   ├── {session_id}/       # Per-run isolated outputs
│   │   ├── config.json     # Full config copy (session-specific)
│   │   ├── {sport}/
│   │   │   ├── haiku.txt
│   │   │   ├── sonnet.txt
│   │   │   └── metadata.json
│   │   ├── analysis_report.md
│   │   ├── execution_log.jsonl      # Detailed provenance
│   │   ├── usage_log.jsonl          # Aggregate analytics
│   │   └── config.changelog.json    # Config changes vs default
│   └── latest -> {session_id}       # Symlink to most recent
└── tests/
    ├── conftest.py          # Shared pytest fixtures
    ├── test_orchestrator.py
    ├── test_poetry_agent.py
    └── test_config_builder.py
```

## Working with This Codebase

### Creating Configuration Files

When users request to run the demo, Claude Code should:
1. Load the default configuration from `config.default.json`
2. Ask for 3-5 sports (or use the provided list)
3. Validate the count
4. Create timestamped config file in `output/configs/config_TIMESTAMP.json` with:
   - sports list
   - retry_enabled setting
   - generation_mode (template or llm)
   - llm config (only if generation_mode is "llm")
5. The orchestrator will:
   - Generate unique session_id at runtime (format: `session_YYYYMMDD_HHMMSS_xxxxxx`)
   - Copy full config to `output/{session_id}/config.json` (session-specific copy)
   - Create changelog in `output/{session_id}/config.changelog.json`

**Usage pattern:**
```python
from config_builder import ConfigBuilder
from datetime import datetime

# Template mode (minimal config)
builder = ConfigBuilder.load_default()
builder.with_sports(["hockey", "swimming", "volleyball"])
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
builder.save(f"output/configs/config_{timestamp}.json")

# LLM mode (auto-populates LLM defaults)
builder = ConfigBuilder.load_default()
builder.with_sports(["hockey", "swimming", "volleyball"])
builder.with_generation_mode("llm")  # Auto-adds llm config
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
builder.save(f"output/configs/config_{timestamp}.json")
```

### Config File Storage Pattern

The system uses a two-location pattern for config files:

1. **Input Location**:
   - `output/configs/config_TIMESTAMP.json` - Timestamped configs created by the skill
   - Used by orchestrator via `--config` flag (required)

2. **Session Copy** (automatic):
   - Orchestrator copies input config to `output/{session_id}/config.json`
   - Makes each session self-contained and reproducible
   - Logged in execution_log.jsonl as `config_copied` event

**Typical workflow:**
```bash
# Create config via skill (saves to output/configs/config_TIMESTAMP.json)
# Claude Code skill handles this interactively

# Run orchestrator with explicit config path
python3 orchestrator.py --config output/configs/config_20251103_204829.json

# Or with default config path (if configured)
python3 orchestrator.py
```

**Self-contained sessions:**
Each session directory contains everything needed to understand/reproduce the run:
- `config.json` - Full configuration used
- `config.changelog.json` - What changed from default
- `execution_log.jsonl` - Complete audit trail
- `{sport}/` - Generated poems and metadata

### Enabling LLM Mode

For real LLM-generated poetry:
1. Check if `TOGETHER_API_KEY` is set: `echo $TOGETHER_API_KEY`
2. If not set, guide user to get free API key from https://www.together.ai/
3. Update config.json with `"generation_mode": "llm"`
4. Ensure requirements.txt is installed: `pip install -r requirements.txt`

### Analyzing Logs

Execution log (detailed provenance):
```bash
cat output/latest/execution_log.jsonl | jq .
cat output/latest/execution_log.jsonl | jq 'select(.action == "failed")'
```

Usage log (aggregate stats):
```bash
cat output/latest/usage_log.jsonl | jq .
```

Configuration changelog (track what changed from default):
```bash
# View changelog for latest session
cat output/latest/config.changelog.json | jq .

# Quick scan: What changed from default?
cat output/latest/config.changelog.json | jq .changed_from_default

# View all session changelogs
find output -name "config.changelog.json" -exec cat {} \; | jq -s .

# Find sessions where sports changed
find output -name "config.changelog.json" -exec jq 'select(.changed_from_default | contains(["sports"]))' {} \;

# Summary of all changes across sessions
find output -name "config.changelog.json" -exec jq '{session: .session_id, changed: .changed_from_default, user: .user, reason: .reason}' {} \;

# Machine audit: Get exact old/new values for specific changes
find output -name "config.changelog.json" -exec jq 'select(.changes.sports) | {session: .session_id, sports: .changes.sports}' {} \;
```

### Retry Behavior

The orchestrator supports optional retries (orchestrator.py:62):
- Default: `retry_enabled=True`
- Each failed agent gets one retry attempt
- Can be disabled by modifying SportsPoetryOrchestrator initialization

### Agent Communication

Agents are spawned as subprocesses (not threads):
- Parent: orchestrator.py
- Child: poetry_agent.py (one per sport)
- Communication via: command-line args, file I/O, and exit codes
- Timeout: 120 seconds per agent (orchestrator.py:156)

## Testing Notes

### Fixtures (tests/conftest.py)

- `temp_session`: Temporary session directory
- `api_key`: Together.ai API key (skips test if unavailable)
- `sample_config`: Pre-configured test config
- `config_file`: Temporary config.json file

### Test Structure

Tests are organized by component:
- `test_orchestrator.py`: Workflow coordination tests
- `test_poetry_agent.py`: Individual agent tests

### Running Tests with Coverage

```bash
pytest --cov=. --cov-report=html
```

## Configuration Change Tracking

### Changelog Format

Location: `output/{session_id}/config.changelog.json`

Each session gets a changelog file that tracks what changed from the default configuration:

```json
{
  "timestamp": "2025-11-03T18:40:00.123456+00:00",
  "session_id": "session_20251103_184000_a3f9c2",
  "user": "orchestrator",
  "reason": "Workflow execution",
  "changed_from_default": ["sports", "generation_mode", "llm"],
  "changes": {
    "sports": {
      "old": ["basketball", "soccer", "tennis"],
      "new": ["hockey", "swimming", "volleyball"]
    },
    "generation_mode": {
      "old": "template",
      "new": "llm"
    }
  }
}
```

**Fields:**
- `timestamp` - When changelog was created (ISO 8601 format)
- `session_id` - Which session this is for (generated at runtime)
- `user` - Who initiated the run (typically "orchestrator")
- `reason` - Explanation of why this run was executed
- `changed_from_default` - Array of field names (quick human scan)
- `changes` - Full old/new values (machine-auditable)

**Key design:**
- Changelog is created by the **orchestrator** at runtime, not by ConfigBuilder
- Compares against `config.default.json` only (stable baseline)
- "old" = value from default template
- "new" = value in current config
- All timestamps use ISO 8601 format exclusively

### Default Configuration

The `config.default.json` file provides a stable baseline for all configs:

```json
{
  "sports": ["basketball", "soccer", "tennis"],
  "retry_enabled": true,
  "generation_mode": "template"
}
```

**Important:**
- This file is checked into git and must exist for the system to work
- It contains only the minimal required fields
- LLM configuration is NOT included (auto-populated when needed)
- Session ID and timestamp are NOT included (generated at runtime)

## Important Implementation Details

1. **Session Directory Creation**: Happens after config read (orchestrator.py:493) to ensure session_id is available
2. **Config Copy**: Full config file copied to session directory (orchestrator.py:497-504) for self-contained sessions
3. **Log File Migration**: Early logs from root are moved to session directory (orchestrator.py:515-523)
4. **Symlink Management**: `output/latest` always points to most recent session (orchestrator.py:124-127)
5. **Thread Safety**: ProvenanceLogger uses threading.Lock for concurrent writes (orchestrator.py:27)
6. **Metadata Tracking**: Each agent writes metadata.json with line counts, word counts, duration (poetry_agent.py:379-394)

## Common Issues

**"No config found"**: Create a config file using the create_config skill or specify path with `--config` flag
**Agent timeout**: Increase timeout value at orchestrator.py:156
**LLM mode fails**: Check API key is set and requirements.txt is installed
**Permission errors on symlink**: Windows may require admin rights; can be disabled if needed
