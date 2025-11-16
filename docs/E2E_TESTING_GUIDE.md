# End-to-End Testing Guide for Claude Code Skills

This guide explains how to test Claude Code skills end-to-end, from simple output validation to full AI behavior testing.

## Table of Contents

1. [Testing Levels](#testing-levels)
2. [Approach Comparison](#approach-comparison)
3. [Approach 1: Output Validation](#approach-1-output-validation)
4. [Approach 2: API Simulation](#approach-2-api-simulation)
5. [Approach 3: Manual Acceptance Testing](#approach-3-manual-acceptance-testing)
6. [Approach 4: Production Monitoring](#approach-4-production-monitoring)
7. [Scaling to Complex Projects](#scaling-to-complex-projects)
8. [Best Practices](#best-practices)
9. [Resources](#resources)

## Testing Levels

### Level 1: Unit Tests ✓ Fast, Cheap, Deterministic

**What**: Test individual functions in isolation
**Example**: `test_api_key_detection_from_environment()`
**Coverage**: 20% of end-to-end behavior
**Cost**: Free, runs in milliseconds
**When to use**: Always - foundation of testing pyramid

```python
def test_check_api_key():
    key = check_api_key("together")
    assert key is not None
```

### Level 2: Integration Tests ✓ Medium Speed, Cheap, Mostly Deterministic

**What**: Test workflow steps working together
**Example**: `test_complete_template_mode_workflow()`
**Coverage**: 60% of end-to-end behavior
**Cost**: Free, runs in hundreds of milliseconds
**When to use**: For every major workflow

```python
def test_complete_workflow():
    builder = ConfigBuilder.load_default()
    builder.with_sports(["basketball", "soccer", "tennis"])
    config_path = builder.save("config.json")

    assert Path(config_path).exists()
    assert json.loads(Path(config_path).read_text())["sports"] == ["basketball", "soccer", "tennis"]
```

### Level 3: API Simulation Tests ~ Slow, Costs Money, Non-Deterministic

**What**: Test Claude's decision-making using API
**Example**: `test_claude_recognizes_skill_trigger()`
**Coverage**: 90% of end-to-end behavior
**Cost**: ~$0.01-0.10 per test run
**When to use**: Critical paths, before major releases

```python
def test_claude_recognizes_skill():
    response = anthropic_client.messages.create(
        model="claude-sonnet-4",
        messages=[{"role": "user", "content": "Create a config for basketball, soccer, tennis"}]
    )
    assert "config" in response.content[0].text.lower()
```

### Level 4: Manual Acceptance Tests ⚠️ Slowest, Free, Human Judgment

**What**: Human tester follows acceptance criteria
**Example**: Manual test scenarios in test file
**Coverage**: 100% including UX and edge cases
**Cost**: Free but requires human time
**When to use**: Before releases, for UX validation

## Approach Comparison

| Approach | Speed | Cost | Determinism | Coverage | Maintenance |
|----------|-------|------|-------------|----------|-------------|
| Unit Tests | ⚡⚡⚡ | Free | ✓✓✓ | 20% | Low |
| Integration Tests | ⚡⚡ | Free | ✓✓ | 60% | Low |
| API Simulation | ⚡ | $$$ | ✗ | 90% | Medium |
| Manual Testing | 🐌 | Time | ✓ | 100% | High |

**Recommended mix for this project:**
- 70% Unit tests (test_create_config_skill.py)
- 20% Integration tests (test_e2e_output_validation.py)
- 5% API simulation (test_e2e_api_simulation.py, test_skill_e2e_complete.py - run before releases)
- 5% Manual testing (acceptance criteria - run before major changes)

## Approach 1: Output Validation

**File**: `tests/test_e2e_output_validation.py`

Tests the complete workflow outputs without testing Claude's decision-making.

### What It Tests

✓ All files are created
✓ Files have correct structure
✓ Files are valid (JSON parses, Python compiles)
✓ Files contain expected content
✓ Performance meets requirements
✓ Error handling works correctly

✗ Claude recognizing when to use skill
✗ Claude's conversation flow
✗ Claude's question asking

### Example Test

```python
def test_complete_template_mode_workflow(self, temp_output_dir):
    """Simulates what the skill should do."""

    # Execute workflow (what Claude should do)
    builder = ConfigBuilder.load_default()
    builder.with_sports(["basketball", "soccer", "tennis"])

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    config_path = temp_output_dir / f"config_{timestamp}.json"
    builder.save(str(config_path))

    script = create_generator_script(...)
    script_path = temp_output_dir / f"generate_config_{timestamp}.py"
    script_path.write_text(script)

    # Validate outcomes
    assert config_path.exists()
    assert script_path.exists()

    with open(config_path) as f:
        config = json.load(f)
    assert config["sports"] == ["basketball", "soccer", "tennis"]
    assert config["generation_mode"] == "template"
```

### When to Use

- ✓ Testing that skill utilities produce correct outputs
- ✓ Regression testing (ensure nothing breaks)
- ✓ CI/CD pipeline (fast, reliable)
- ✓ Development (quick feedback loop)

### Running the Tests

```bash
# Run all output validation tests
pytest tests/test_e2e_output_validation.py -v

# Run specific test
pytest tests/test_e2e_output_validation.py::TestE2EOutputValidation::test_complete_template_mode_workflow -v

# Run with coverage
pytest tests/test_e2e_output_validation.py --cov=.claude/skills/create_config
```

## Approach 2: API Simulation

**Files**:
- `tests/test_e2e_api_simulation.py` - Basic Claude behavior validation
- `tests/test_skill_e2e_complete.py` - Comprehensive end-to-end workflow tests

Tests Claude's actual decision-making using the Anthropic API.

### What It Tests

✓ Claude recognizes skill triggers
✓ Claude validates input correctly
✓ Claude handles errors appropriately
✓ Claude's conversation flow

✗ Actual file creation (requires tool execution)
✗ Complex multi-turn conversations (expensive)

### Example Tests

**Basic Recognition Test** (test_e2e_api_simulation.py):
```python
@pytest.mark.api  # Mark as API test
def test_claude_recognizes_skill_trigger(self, anthropic_client, skill_context):
    """Test Claude recognizes when to use create_config skill."""

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1000,
        system=f"You have access to a create_config skill.\n\n{skill_context}",
        messages=[{
            "role": "user",
            "content": "Create a config for basketball, soccer, and tennis"
        }]
    )

    response_text = response.content[0].text.lower()

    # Claude should recognize this as config creation
    assert "config" in response_text
    assert any(sport in response_text for sport in ["basketball", "soccer", "tennis"])
```

**Comprehensive Workflow Test** (test_skill_e2e_complete.py):
```python
@pytest.mark.api
def test_validation_error_recovery(self, anthropic_client, skill_context):
    """Test multi-turn conversation with validation error recovery."""

    # Turn 1: Invalid request (only 2 sports)
    response1 = anthropic_client.messages.create(...)
    assert any(keyword in response1_text.lower()
               for keyword in ["3", "more", "additional"])

    # Turn 2: User adds another sport
    response2 = anthropic_client.messages.create(
        messages=[
            {"role": "user", "content": "Create a config for tennis and golf"},
            {"role": "assistant", "content": response1_text},
            {"role": "user", "content": "Add baseball"}
        ]
    )

    # Claude should proceed after correction
    assert "config" in response2_text.lower()
```

### Setup Requirements

1. Install Anthropic SDK:
```bash
pip install anthropic
```

2. Set API key:
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

3. Run API tests:
```bash
# Run only API tests
pytest -m api -v

# Skip API tests (for CI/CD)
pytest -m "not api" -v
```

### Cost Considerations

Each test costs approximately:
- Claude Sonnet: ~$0.01 per test
- Claude Opus: ~$0.05 per test
- Claude Haiku: ~$0.001 per test

**Strategy**: Run these tests sparingly:
- Before major releases
- When changing skill logic
- To validate across different models
- Not in CI/CD (too expensive)

### When to Use

- ✓ Testing Claude's understanding of the skill
- ✓ Validating skill description clarity
- ✓ Testing across different models (Opus, Sonnet, Haiku)
- ✓ Before major skill changes
- ✗ Regular CI/CD (too expensive)
- ✗ Every code commit (too slow)

## Approach 3: Manual Acceptance Testing

**File**: Documented in `tests/test_create_config_skill.py` as docstrings

Manual testing following acceptance criteria to validate complete UX.

### Example Acceptance Criteria

```
ACCEPTANCE CRITERIA (Test manually with Claude Code):

1. User input: "Create a config for basketball, soccer, and tennis"

2. Expected Claude behavior WITH skill:
   - Recognizes this as create_config task
   - Does NOT ask about mode (uses template default)
   - Creates TWO files:
     * output/configs/config_{timestamp}.json
     * output/configs/generate_config_{timestamp}.py
   - Generator script is executable (chmod +x)
   - Completes in <5 seconds
   - Reports both file paths to user

3. Success criteria:
   ✓ Both files exist
   ✓ Config is valid JSON with correct fields
   ✓ Generator script is valid Python and executable
   ✓ Running generator script creates new config with new timestamp

4. Run this test on: Claude Sonnet 4 (primary target)
```

### How to Run Manual Tests

#### Test 1: Quick Start (Template Mode)

**Input**:
```
Create a config for basketball, soccer, and tennis
```

**Validate**:
```bash
# 1. Check both files were created
ls -lh output/configs/

# 2. Verify config structure
cat output/configs/config_*.json | jq .

# 3. Check script is executable
ls -l output/configs/generate_config_*.py
# Should show: -rwxr-xr-x

# 4. Run generator script
./output/configs/generate_config_*.py

# 5. Verify new config was created
ls -lt output/configs/config_*.json | head -2
```

#### Test 2: LLM Mode

**Setup**:
```bash
export TOGETHER_API_KEY="your-key-here"
```

**Input**:
```
Create an LLM mode config for hockey, swimming, volleyball
```

**Validate**:
```bash
# Check LLM config structure
cat output/configs/config_*.json | jq '.generation_mode, .llm'
# Should show:
# "llm"
# {
#   "provider": "together",
#   "model": "..."
# }
```

#### Test 3: Error Recovery

**Input** (intentionally invalid):
```
Create a config for basketball and soccer
```

**Expected**:
- Claude catches error
- Reports: "You provided 2 sports, but we need 3-5"
- Suggests adding one more
- Waits for user correction

**Follow-up**:
```
Add tennis
```

**Expected**:
- Claude adds tennis to list
- Creates valid config

### When to Use Manual Testing

- ✓ Before major releases
- ✓ Testing UX and conversation flow
- ✓ Validating new features
- ✓ Cross-model validation (test on Opus, Sonnet, Haiku)
- ✓ Edge cases that are hard to automate

## Approach 4: Production Monitoring

For complex projects, add runtime monitoring to catch issues in production.

### Example: Telemetry

```python
def create_config_with_telemetry(sports, mode):
    """Wrapper that logs usage and errors."""
    start_time = time.time()

    try:
        # Execute workflow
        builder = ConfigBuilder.load_default()
        builder.with_sports(sports)
        # ... rest of workflow

        # Log success
        log_telemetry({
            "event": "config_created",
            "duration": time.time() - start_time,
            "sports_count": len(sports),
            "mode": mode,
            "success": True
        })

    except Exception as e:
        # Log failure
        log_telemetry({
            "event": "config_creation_failed",
            "duration": time.time() - start_time,
            "error": str(e),
            "sports_count": len(sports),
            "mode": mode,
            "success": False
        })
        raise
```

### Monitoring Metrics

Track:
- Success rate (should be >95%)
- Average completion time (should be <5s for template mode)
- Error types and frequencies
- Usage patterns (which modes, how many sports)

## Scaling to Complex Projects

As projects grow, testing strategies need to scale:

### Small Projects (like this one)

**Testing Mix**:
- 70% Unit tests
- 20% Integration tests
- 10% Manual acceptance tests

**CI/CD**:
```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    pytest tests/test_create_config_skill.py
    pytest tests/test_e2e_output_validation.py
```

### Medium Projects (10+ skills)

**Testing Mix**:
- 60% Unit tests
- 25% Integration tests
- 10% API simulation (critical paths only)
- 5% Manual acceptance tests

**CI/CD**:
```yaml
- name: Run fast tests
  run: pytest -m "not api"

- name: Run API tests (on main branch only)
  if: github.ref == 'refs/heads/main'
  run: pytest -m api
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

### Large Projects (50+ skills, production)

**Testing Mix**:
- 50% Unit tests
- 30% Integration tests
- 15% API simulation
- 5% Manual acceptance tests
- Production monitoring

**Additional Strategies**:

1. **Skill Categories**: Group related skills
2. **Smoke Tests**: Quick tests covering critical paths
3. **Regression Suite**: Tests for previously found bugs
4. **Performance Benchmarks**: Track execution time over releases
5. **User Acceptance Testing**: Real users test in staging environment

**Example Test Organization**:
```
tests/
├── unit/
│   ├── test_skill_helpers.py
│   └── test_config_builder.py
├── integration/
│   ├── test_e2e_output_validation.py
│   └── test_multi_skill_workflows.py
├── api/
│   ├── test_skill_recognition.py
│   └── test_conversation_flow.py
├── acceptance/
│   ├── MANUAL_TEST_CHECKLIST.md
│   └── test_scenarios.py
└── performance/
    └── test_benchmarks.py
```

## Best Practices

### 1. Test Pyramid

Maintain the right balance:

```
        ◢◣     Manual Tests (5%)
      ◢    ◣
    ◢        ◣  API Simulation (10%)
  ◢            ◣
◢  Integration  ◣ (25%)
◢                ◣
◢                  ◣
◢    Unit Tests     ◣ (60%)
◢____________________◣
```

### 2. Fail Fast

Tests should fail quickly and clearly:

```python
# Good
assert config["sports"] == expected_sports, \
    f"Sports mismatch. Expected {expected_sports}, got {config['sports']}"

# Bad
assert config["sports"] == expected_sports
```

### 3. Independent Tests

Each test should be independent:

```python
# Good - uses temp directory
def test_with_isolation(temp_output_dir):
    config_path = temp_output_dir / "config.json"
    # Test creates files in isolation

# Bad - shares state
def test_with_shared_state():
    config_path = "output/config.json"  # Conflicts with other tests
```

### 4. Clear Test Names

Names should describe what's being tested:

```python
# Good
def test_complete_template_mode_workflow():
def test_validation_error_when_too_few_sports():

# Bad
def test_1():
def test_config():
```

### 5. Document What's NOT Tested

Be explicit about test limitations:

```python
def test_config_creation():
    """
    Tests config file creation.

    Coverage:
    ✓ File is created
    ✓ JSON is valid
    ✓ Required fields present

    NOT tested (requires manual validation):
    ✗ Claude's decision to use skill
    ✗ Conversation flow
    ✗ UX quality
    """
```

### 6. Use Test Markers

Organize tests with pytest markers:

```python
@pytest.mark.api  # Requires API key, costs money
@pytest.mark.slow  # Takes >1 second
@pytest.mark.integration  # Integration test
@pytest.mark.manual  # Manual test scenario
```

Run specific test categories:
```bash
pytest -m "not api"  # Skip expensive tests
pytest -m integration  # Run only integration tests
```

### 7. Test Error Paths

Don't just test happy paths:

```python
def test_error_when_no_api_key():
    """Verify helpful error when API key missing."""
    # Clear API key
    if "TOGETHER_API_KEY" in os.environ:
        del os.environ["TOGETHER_API_KEY"]

    key = check_api_key("together")
    assert key is None

    # Verify setup instructions are helpful
    instructions = get_setup_instructions("together")
    assert "together.ai" in instructions
    assert "TOGETHER_API_KEY" in instructions
```

## Resources

### Testing Frameworks

- **pytest**: Python testing framework (https://pytest.org)
- **pytest-cov**: Coverage reporting (https://pytest-cov.readthedocs.io)
- **anthropic**: Claude API SDK (https://docs.anthropic.com)

### Related Documentation

- `tests/test_create_config_skill.py`: Unit tests for skill (11 tests)
- `tests/test_e2e_output_validation.py`: Integration tests (Approach 1, 4 tests)
- `tests/test_e2e_api_simulation.py`: Basic API simulation tests (Approach 2, 4 tests)
- `tests/test_skill_e2e_complete.py`: Comprehensive E2E API tests (Approach 2, 7 tests)
- `.claude/skills/create_config/SKILL.md`: Skill documentation

### Learning Resources

- **Testing AI Agents**: https://www.anthropic.com/research/testing-ai-agents
- **Evaluation-First Development**: Build tests before implementing features
- **Test-Driven Development (TDD)**: Write tests, then code

### Example Commands

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_e2e_output_validation.py

# Run tests matching pattern
pytest -k "validation"

# Run with coverage
pytest --cov=. --cov-report=html

# Run fast tests only (skip API)
pytest -m "not api"

# Run verbose
pytest -v

# Run and show print statements
pytest -s
```

## Summary

For this sports poetry project:

1. **Start with Approach 1** (Output Validation)
   - Fast, reliable, cheap
   - Tests the workflow outputs
   - Good for CI/CD

2. **Add Approach 3** (Manual Testing)
   - Test UX and conversation flow
   - Before releases
   - Documented acceptance criteria

3. **Optionally add Approach 2** (API Simulation)
   - Before major releases
   - Cross-model validation
   - When skill logic changes significantly

4. **For complex projects, add Approach 4** (Monitoring)
   - Production telemetry
   - Error tracking
   - Usage analytics

**Key Principle**: Test outcomes, not exact behavior. AI is non-deterministic, so focus on validating results rather than specific paths to get there.
