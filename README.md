# Sports Poetry Multi-Agent Workflow Demo

A demonstration of Claude Code's multi-agent coordination capabilities, with full auditability and provenance tracking.

## Overview

This demo showcases how to build agentic workflows with:
- **Conversational input collection** - Natural dialogue with Claude
- **Parallel agent execution** - Multiple agents working simultaneously
- **Graceful error handling** - Continues despite failures
- **Comprehensive logging** - Full provenance and analytics
- **Result synthesis** - Final agent analyzes all outputs

## What It Does

1. **You tell Claude** which 3-5 sports you want poems about
2. **Claude validates** and writes `config.json`
3. **Orchestrator launches** parallel poetry agents (one per sport)
4. **Each agent generates** a haiku and sonnet about their sport
5. **Analyzer agent** compares all poems and creates a report
6. **Logs capture** everything for auditability and improvement

## Quick Start

### Step 1: Provide Sports to Claude

Just chat with Claude Code:

```
You: Let's run the demo! I want poems about basketball, soccer, and tennis.

Claude: Great! I'll validate that and create the config file...
```

Claude will:
- Validate you have 3-5 sports
- Confirm the list with you
- Write `config.json`

### Step 2: Run the Orchestrator

```bash
cd sports_poetry_demo
python3 orchestrator.py
```

Watch the output as agents work in parallel:

```
[orchestrator] Reading configuration file
[orchestrator] Loaded config: 3 sports
[orchestrator] Launching 3 agents in parallel
[orchestrator] Launching poetry agent for basketball (attempt 1)
[orchestrator] Launching poetry agent for soccer (attempt 1)
[orchestrator] Launching poetry agent for tennis (attempt 1)
Agent basketball: Starting poetry generation
Agent soccer: Starting poetry generation
Agent tennis: Starting poetry generation
Agent basketball: Wrote haiku (3 lines)
Agent soccer: Wrote haiku (3 lines)
Agent tennis: Wrote haiku (3 lines)
Agent basketball: Wrote sonnet (14 lines)
Agent soccer: Wrote sonnet (14 lines)
Agent tennis: Wrote sonnet (14 lines)
Agent basketball: Complete
Agent soccer: Complete
Agent tennis: Complete
[orchestrator] All agents complete: 3 succeeded, 0 failed
[orchestrator] Launching analyzer agent
Analyzer: Starting analysis
Analyzer: Found 3 sports to analyze
Analyzer: Wrote analysis report
Analyzer: Complete
[analyzer] Analysis complete in 0.2s
[orchestrator] Usage log written. Total workflow time: 8.4s
[orchestrator] Workflow completed successfully
```

### Step 3: View Results

Check the `output/` directory:

```
output/
├── basketball/
│   ├── haiku.txt          # 3-line haiku about basketball
│   ├── sonnet.txt         # 14-line sonnet about basketball
│   └── metadata.json      # Line counts, word counts, timestamps
├── soccer/
│   ├── haiku.txt
│   ├── sonnet.txt
│   └── metadata.json
├── tennis/
│   ├── haiku.txt
│   ├── sonnet.txt
│   └── metadata.json
└── analysis_report.md     # Comparative analysis of all poems
```

Read the analysis report:

```bash
cat output/analysis_report.md
```

### Step 4: Review Logs

**Detailed provenance** (every action):
```bash
cat execution_log.jsonl | jq .
```

**Usage analytics** (aggregate stats):
```bash
cat usage_log.jsonl | jq .
```

## Architecture

```
User ↔ Claude (natural language)
         ↓
    config.json
         ↓
  orchestrator.py
         ↓
    ┌────┴────┬────────┬────────┐
    ▼         ▼        ▼        ▼
Agent 1   Agent 2  Agent 3  Agent N  (parallel)
    │         │        │        │
    └────┬────┴────────┴────────┘
         ▼
   Analyzer Agent
         ↓
  analysis_report.md
  execution_log.jsonl
  usage_log.jsonl
```

## Files

### Input
- `config.json` - Created by Claude from your input

### Scripts
- `orchestrator.py` - Main coordinator
- `poetry_agent.py` - Generates poems for one sport
- `analyzer_agent.py` - Synthesizes results

### Output
- `output/{sport}/haiku.txt` - Generated haikus
- `output/{sport}/sonnet.txt` - Generated sonnets
- `output/{sport}/metadata.json` - Poem metadata
- `output/analysis_report.md` - Final analysis

### Logs
- `execution_log.jsonl` - Detailed provenance (every action)
- `usage_log.jsonl` - Aggregate analytics (per run)

## Log Examples

### execution_log.jsonl

One event per line, showing exact actor, action, and timing:

```json
{"timestamp": 1730476980.123, "timestamp_iso": "2025-11-01T13:03:00Z", "actor": "orchestrator", "action": "read_config", "message": "Reading configuration file"}
{"timestamp": 1730476980.234, "actor": "orchestrator", "action": "config_loaded", "details": {"sports": ["basketball", "soccer", "tennis"], "sports_count": 3}}
{"timestamp": 1730476980.345, "actor": "orchestrator", "action": "launch_agent", "details": {"sport": "basketball", "attempt": 1}}
{"timestamp": 1730476982.456, "actor": "agent_basketball", "action": "complete", "details": {"duration_s": 2.1, "haiku_lines": 3, "sonnet_lines": 14}}
```

**Use cases:**
- Debug which agent failed and when
- Prove which agent created which file
- Reconstruct exact execution timeline
- Identify performance bottlenecks

### usage_log.jsonl

One entry per workflow run:

```json
{
  "session_id": "abc123",
  "timestamp": "2025-11-01T13:03:00Z",
  "sports": ["basketball", "soccer", "tennis"],
  "sports_count": 3,
  "agents_launched": 3,
  "agents_succeeded": 3,
  "agents_failed": 0,
  "agent_results": [
    {"sport": "basketball", "status": "success", "duration_s": 2.1},
    {"sport": "soccer", "status": "success", "duration_s": 2.3},
    {"sport": "tennis", "status": "success", "duration_s": 1.9}
  ],
  "total_duration_s": 8.4,
  "errors": []
}
```

**Use cases:**
- Analyze failure patterns over time
- Track most popular sports
- Measure performance trends
- Identify systematic issues

## Error Handling

The workflow uses **graceful degradation**:

1. Each agent runs once
2. If it fails, optionally retry once
3. Continue with other agents regardless
4. Log all failures with full details
5. Analyzer notes missing sports in report

**Example with failure:**

```bash
# Agent for "hockey" fails
[orchestrator] Launching poetry agent for hockey (attempt 1)
[agent_hockey] failed: FileNotFoundError...
[orchestrator] Retrying hockey agent
[agent_hockey] failed: FileNotFoundError...
[orchestrator] All agents complete: 2 succeeded, 1 failed

# Workflow continues, analyzer notes the gap
# Logs capture exactly what happened
```

## LLM-Based Poetry Generation

The demo supports two generation modes:

### Template Mode (Default)

Uses pre-written haiku and sonnet templates. Fast, free, and reliable.

```json
{
  "generation_mode": "template"
}
```

### LLM Mode

Generates unique, creative poems using a language model. Requires API access.

```json
{
  "generation_mode": "llm",
  "llm_provider": "together",
  "llm_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
}
```

### Setup for LLM Mode

#### Option 1: Together.ai (Recommended - Free Tier Available)

1. Sign up at https://www.together.ai/
2. Get your API key from https://api.together.xyz/settings/api-keys
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set your API key:
   ```bash
   export TOGETHER_API_KEY="your-api-key-here"
   ```
5. Update `config.json`:
   ```json
   {
     "generation_mode": "llm",
     "llm_provider": "together",
     "llm_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
   }
   ```

Available free models on Together.ai:
- `meta-llama/Llama-3.3-70B-Instruct-Turbo-Free` (recommended)
- `meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo-Free`
- `meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo-Free`

See more at: https://www.together.ai/models

#### Option 2: HuggingFace Inference API

1. Sign up at https://huggingface.co/
2. Get your API token from https://huggingface.co/settings/tokens
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set your API token:
   ```bash
   export HUGGINGFACE_API_TOKEN="your-token-here"
   ```
5. Update `config.json`:
   ```json
   {
     "generation_mode": "llm",
     "llm_provider": "huggingface",
     "llm_model": "meta-llama/Meta-Llama-3-8B-Instruct"
   }
   ```

### Running with LLM Mode

Once configured, run normally:

```bash
python3 orchestrator.py
```

You'll see LLM-specific output:

```
[orchestrator] Launching poetry agent for basketball (attempt 1)
Agent basketball: Starting poetry generation (mode: llm, provider: together)
Agent basketball: Wrote haiku (3 lines)
Agent basketball: Wrote sonnet (14 lines)
Agent basketball: Complete
```

The generated poems will be unique for each sport and each run!

## Customization

### Add More Sports

Just tell Claude! No code changes needed:

```
You: Let's do 5 sports this time: basketball, soccer, tennis, swimming, and volleyball
```

### Disable Retries

Edit `orchestrator.py`:

```python
orchestrator = SportsPoetryOrchestrator(retry_enabled=False)
```

### Add More Poetry Forms

1. Update `poetry_agent.py` to generate limerick, villanelle, etc.
2. Update `analyzer_agent.py` to analyze new forms
3. Update `metadata.json` structure

### Switch Generation Modes

Template mode (fast, deterministic):
```bash
# Edit config.json
{
  "generation_mode": "template"
}
```

LLM mode (creative, unique):
```bash
# Edit config.json
{
  "generation_mode": "llm",
  "llm_provider": "together",
  "llm_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
}
```

## Advanced Usage

### Analyze Logs with jq

Find all failures:
```bash
cat execution_log.jsonl | jq 'select(.action == "failed")'
```

Average agent duration:
```bash
cat usage_log.jsonl | jq '.agent_results[].duration_s' | jq -s 'add/length'
```

Most popular sports:
```bash
cat usage_log.jsonl | jq -r '.sports[]' | sort | uniq -c | sort -rn
```

### Run Multiple Times

The logs append, so you can run multiple times and analyze trends:

```bash
# Run 5 times with different sports
python3 orchestrator.py
python3 orchestrator.py
python3 orchestrator.py

# Analyze trends
cat usage_log.jsonl | jq -s '.[].total_duration_s' | jq -s 'add/length'
```

## Troubleshooting

**Problem**: `ModuleNotFoundError`
- **Solution**: Ensure you're using Python 3.7+, all modules are in stdlib

**Problem**: Agents timeout
- **Solution**: Increase timeout in `orchestrator.py` line 87

**Problem**: No poems generated
- **Solution**: Check `execution_log.jsonl` for error details

**Problem**: Analysis report is empty
- **Solution**: Ensure `output/*/` directories have haiku.txt and sonnet.txt

## Learning Points

This demo demonstrates:

1. **Conversational Input** - Natural language → structured config
2. **Parallel Execution** - Multiple agents running simultaneously
3. **Provenance Logging** - Every action tracked with timestamps
4. **Graceful Degradation** - Failures don't stop the workflow
5. **Result Synthesis** - Final agent aggregates all outputs
6. **Auditability** - Can prove exactly what happened when
7. **Iterative Improvement** - Logs enable data-driven enhancement

## Next Steps

- Add web UI for real-time monitoring
- Implement more poetry forms
- Use actual LLM for generation
- Add human feedback collection
- Create dashboards from usage logs
- A/B test different prompting strategies

## Documentation

- See `SPEC.md` for detailed specification
- See source code comments for implementation details
- See logs for execution traces

## License

MIT - Use this as a template for your own multi-agent workflows!

---

**Built with Claude Code** - Demonstrating agentic AI workflows
