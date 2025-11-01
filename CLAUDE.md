# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Sports Poetry Multi-Agent Workflow Demo** that showcases multi-agent coordination with parallel execution, provenance logging, and result synthesis.

**Workflow**: User provides sports list → Claude validates and creates config.json → Orchestrator launches parallel poetry agents → Each agent generates haiku + sonnet → Analyzer synthesizes results → Full audit logs created

## Common Commands

### Running the Demo

```bash
cd sports_poetry_demo
python3 orchestrator.py
```

Requires a valid `config.json` file in the sports_poetry_demo directory. Claude Code typically creates this file interactively based on user input.

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

The `config.json` structure:
```json
{
  "sports": ["basketball", "soccer", "tennis"],
  "session_id": "unique_id",
  "generation_mode": "template" | "llm",
  "llm_provider": "together" | "huggingface",
  "llm_model": "model-name"
}
```

**Generation Modes**:
- `template` (default): Fast, deterministic, uses pre-written templates
- `llm`: Calls Together.ai or HuggingFace API for unique poems (requires API key)

### Directory Structure

```
sports_poetry_demo/
├── orchestrator.py          # Main workflow coordinator
├── poetry_agent.py          # Individual poetry generator
├── analyzer_agent.py        # Result synthesis
├── config.json              # Runtime configuration (created by Claude)
├── output/
│   ├── {session_id}/       # Per-run isolated outputs
│   │   ├── {sport}/
│   │   │   ├── haiku.txt
│   │   │   ├── sonnet.txt
│   │   │   └── metadata.json
│   │   ├── analysis_report.md
│   │   ├── execution_log.jsonl    # Detailed provenance
│   │   └── usage_log.jsonl        # Aggregate analytics
│   └── latest -> {session_id}     # Symlink to most recent
└── tests/
    ├── conftest.py          # Shared pytest fixtures
    ├── test_orchestrator.py
    └── test_poetry_agent.py
```

## Working with This Codebase

### Creating config.json

When users request to run the demo, Claude Code should:
1. Ask for 3-5 sports (or use the provided list)
2. Validate the count
3. Create `sports_poetry_demo/config.json` with:
   - sports list
   - unique session_id (e.g., timestamp-based)
   - timestamp
   - default to template mode unless LLM requested

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

## Important Implementation Details

1. **Session Directory Creation**: Happens after config read (orchestrator.py:431) to ensure session_id is available
2. **Log File Migration**: Early logs from root are moved to session directory (orchestrator.py:434-445)
3. **Symlink Management**: `output/latest` always points to most recent session (orchestrator.py:124-127)
4. **Thread Safety**: ProvenanceLogger uses threading.Lock for concurrent writes (orchestrator.py:27)
5. **Metadata Tracking**: Each agent writes metadata.json with line counts, word counts, duration (poetry_agent.py:379-394)

## Common Issues

**"No config found"**: Create config.json in sports_poetry_demo/ directory
**Agent timeout**: Increase timeout value at orchestrator.py:156
**LLM mode fails**: Check API key is set and requirements.txt is installed
**Permission errors on symlink**: Windows may require admin rights; can be disabled if needed
