# E2E Testing Quick Start

Quick reference for running different types of tests.

## Test Files Overview

| File | Type | Speed | Cost | When to Run |
|------|------|-------|------|-------------|
| `test_create_config_skill.py` | Unit | ⚡⚡⚡ | Free | Every commit |
| `test_e2e_output_validation.py` | Integration | ⚡⚡ | Free | Every commit |
| `test_e2e_api_simulation.py` | API | ⚡ | $$$ | Before releases |

## Quick Commands

```bash
# Run everything (fast tests only)
pytest

# Run specific test type
pytest tests/test_create_config_skill.py          # Unit tests
pytest tests/test_e2e_output_validation.py        # Integration tests
pytest tests/test_e2e_api_simulation.py -m api    # API tests (costs money!)

# Skip expensive tests
pytest -m "not api"

# Verbose output
pytest -v

# With coverage
pytest --cov=.claude/skills/create_config --cov-report=html
```

## Test What You've Built

### 1. Unit Tests (Foundation)

Tests individual helper functions:

```bash
pytest tests/test_create_config_skill.py -v
```

Expected: 11 tests pass in <1 second

### 2. Integration Tests (Workflow Validation)

Tests complete workflows produce correct outputs:

```bash
pytest tests/test_e2e_output_validation.py -v
```

Expected: 4 tests pass in <1 second

**What's tested**:
- ✓ Template mode config creation
- ✓ LLM mode config creation
- ✓ Validation error handling
- ✓ Performance (<5 seconds)

### 3. API Tests (Claude Behavior)

Tests Claude's actual decision-making:

```bash
# First, set API key
export ANTHROPIC_API_KEY="your-key-here"

# Run API tests
pytest tests/test_e2e_api_simulation.py -m api -v
```

**Cost**: ~$0.05 per full test run

**What's tested**:
- ✓ Claude recognizes skill triggers
- ✓ Claude validates sports count
- ✓ Claude handles missing API keys

### 4. Manual Tests (Complete UX)

Follow acceptance criteria in test file:

```bash
# Open test file to see acceptance criteria
cat tests/test_create_config_skill.py | grep -A 30 "ACCEPTANCE CRITERIA"

# Then test manually with Claude Code
claude
> Create a config for basketball, soccer, and tennis

# Validate results
ls -lh output/configs/
cat output/configs/config_*.json | jq .
./output/configs/generate_config_*.py
```

## Understanding Test Coverage

```
┌─────────────────────────────────────────────────┐
│ What Each Test Level Covers                     │
├─────────────────────────────────────────────────┤
│                                                  │
│ Unit Tests (60% coverage)                       │
│ ▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░                            │
│ - Helper functions work                         │
│ - Validation logic correct                      │
│ - Error messages helpful                        │
│                                                  │
│ Integration Tests (25% additional)              │
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░                            │
│ + Workflow produces correct files               │
│ + Files have correct structure                  │
│ + Performance meets requirements                │
│                                                  │
│ API Tests (10% additional)                      │
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░                            │
│ + Claude recognizes skill                       │
│ + Claude validates input                        │
│ + Claude handles errors                         │
│                                                  │
│ Manual Tests (5% additional)                    │
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ (100%)                     │
│ + UX quality                                    │
│ + Conversation flow                             │
│ + Edge cases                                    │
│                                                  │
└─────────────────────────────────────────────────┘
```

## Interpreting Results

### All Tests Pass ✓

```
====== 19 passed in 1.23s ======
```

**Meaning**: All workflows produce correct outputs

**Next steps**:
- Optional: Run manual tests for UX validation
- Optional: Run API tests before major release

### Some Tests Fail ✗

```
====== 1 failed, 18 passed in 1.45s ======
```

**Common causes**:
1. Missing dependencies: `pip install -r requirements-dev.txt`
2. Missing files: Ensure `config.default.json` exists
3. Logic errors: Check test output for details

**Debugging**:
```bash
# Run failed test with verbose output
pytest tests/test_file.py::test_name -v -s

# Show full error traceback
pytest --tb=long
```

### API Tests Skipped

```
====== 2 skipped ======
```

**Reason**: No `ANTHROPIC_API_KEY` set

**To run**:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
pytest -m api
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        pip install -r requirements-dev.txt

    - name: Run fast tests
      run: |
        pytest -m "not api" --cov=.claude/skills/create_config

    - name: Run API tests (main branch only)
      if: github.ref == 'refs/heads/main'
      run: |
        pytest -m api
      env:
        ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Troubleshooting

### Import Errors

```
ImportError: cannot import name 'ConfigBuilder'
```

**Fix**: Ensure you're in the project root:
```bash
cd sports_poetry_demo
pytest
```

### API Key Issues

```
pytest.skip: ANTHROPIC_API_KEY not set
```

**Fix**: Set API key for API tests:
```bash
export ANTHROPIC_API_KEY="your-key"
pytest -m api
```

### Module Not Found

```
ModuleNotFoundError: No module named 'anthropic'
```

**Fix**: Install dependencies:
```bash
pip install -r requirements-dev.txt
pip install anthropic  # For API tests
```

## Next Steps

1. **Run all fast tests**: `pytest -m "not api" -v`
2. **Check coverage**: `pytest --cov=.claude/skills/create_config`
3. **Read full guide**: `docs/E2E_TESTING_GUIDE.md`
4. **Try manual tests**: Follow acceptance criteria
5. **Optional - API tests**: Set up API key and run API tests

## Learning Path

1. **Start here**: Run unit tests, understand what they test
2. **Next**: Run integration tests, see how workflows are validated
3. **Then**: Read full testing guide for concepts
4. **Advanced**: Try API tests to see Claude behavior testing
5. **Expert**: Add your own tests for new features

## Questions?

- **"Should I run API tests?"** - Only before releases (they cost money)
- **"Are manual tests required?"** - Before major changes, yes
- **"What's the minimum for CI/CD?"** - Unit + Integration tests
- **"How do I test my own skill?"** - Follow the patterns in these test files

For more details, see `docs/E2E_TESTING_GUIDE.md`
