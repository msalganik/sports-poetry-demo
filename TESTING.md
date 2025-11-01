# Testing Guide

This document explains how to test the Sports Poetry Demo using **pytest**.

## Quick Start

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov

# Run only fast tests (skip LLM/API tests)
pytest -m "not requires_api_key"
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_poetry_agent.py     # Unit tests for poem generation
└── test_orchestrator.py     # Integration tests for full workflow
```

## Running Tests

### All Tests
```bash
pytest
```

### With Verbose Output
```bash
pytest -v
```

### Specific Test File
```bash
pytest tests/test_poetry_agent.py
```

### Specific Test
```bash
pytest tests/test_poetry_agent.py::TestTemplateMode::test_generate_haiku_basketball
```

### Fast Tests Only (No API Calls)
```bash
pytest -m "not requires_api_key"
```

### With Coverage Report
```bash
pytest --cov=. --cov-report=html
# Open htmlcov/index.html in browser
```

## Test Categories

### Unit Tests (`test_poetry_agent.py`)

Test individual functions in isolation:

- **Template Mode**: Haiku/sonnet generation with templates
- **Word Counting**: count_words() function
- **LLM Mode**: Poem generation with Together.ai API
- **Error Handling**: Clear errors when misconfigured

**Example:**
```bash
# Run all unit tests
pytest tests/test_poetry_agent.py -v
```

### Integration Tests (`test_orchestrator.py`)

Test full workflows end-to-end:

- **Template Workflow**: Full orchestrator run with template mode
- **Logging**: Verify logs are created
- **Session Directories**: Check output structure

**Example:**
```bash
# Run integration tests
pytest tests/test_orchestrator.py -v
```

## Test Markers

Tests are organized with markers:

- `@pytest.mark.unit` - Fast unit tests
- `@pytest.mark.integration` - Full workflow tests
- `@pytest.mark.requires_api_key` - Needs Together.ai API key
- `@pytest.mark.slow` - Takes >5 seconds

**Run specific markers:**
```bash
# Only unit tests
pytest -m unit

# Only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

## Fixtures

Shared test fixtures in `conftest.py`:

### `temp_session`
Creates a temporary session directory for tests.

```python
def test_something(temp_session):
    # temp_session is a Path to temp directory
    output_file = temp_session / "output.txt"
    output_file.write_text("test")
    assert output_file.exists()
```

### `api_key`
Loads Together.ai API key from environment or file. Skips test if not available.

```python
@pytest.mark.requires_api_key
def test_llm(api_key):
    # api_key is the Together.ai API key
    # Test is skipped if no key available
    pass
```

### `sample_config`
Provides a sample config dictionary for tests.

```python
def test_config(sample_config):
    assert sample_config["generation_mode"] == "template"
    assert len(sample_config["sports"]) == 3
```

## Coverage

### Generate Coverage Report
```bash
pytest --cov=. --cov-report=html --cov-report=term
```

**Output:**
```
---------- coverage: platform linux, python 3.13 -----------
Name                    Stmts   Miss  Cover
-------------------------------------------
orchestrator.py           156     45    71%
poetry_agent.py            98     15    85%
analyzer_agent.py          67     67     0%
-------------------------------------------
TOTAL                     321    127    60%
```

### View HTML Report
```bash
# Generate HTML coverage report
pytest --cov=. --cov-report=html

# Open in browser (macOS)
open htmlcov/index.html

# Open in browser (Linux)
xdg-open htmlcov/index.html
```

## LLM Mode Testing

LLM tests require a Together.ai API key.

### Setup API Key

**Option 1: File** (Recommended)
```bash
echo "your-api-key-here" > ~/together_api_key.txt
```

**Option 2: Environment Variable**
```bash
export TOGETHER_API_KEY="your-api-key-here"
```

### Run LLM Tests
```bash
# Run all tests including LLM
pytest

# Run only LLM tests
pytest -m requires_api_key
```

If no API key is available, LLM tests are automatically skipped:
```
tests/test_poetry_agent.py::test_llm_mode SKIPPED (No API key available)
```

## Common Commands

```bash
# Quick check (fast tests only)
pytest -m "not requires_api_key" -v

# Full test suite
pytest -v

# With coverage
pytest --cov

# Parallel execution (faster)
pytest -n auto

# Stop on first failure
pytest -x

# Show print statements
pytest -s

# Run last failed tests
pytest --lf

# Verbose with coverage
pytest -v --cov=. --cov-report=term-missing
```

## Continuous Integration

For CI/CD (GitHub Actions), use:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      - name: Run tests
        run: pytest -v --cov
      - name: Check coverage
        run: pytest --cov --cov-fail-under=80
```

## Writing New Tests

### Unit Test Template
```python
# tests/test_poetry_agent.py

@pytest.mark.unit
def test_new_feature():
    """Test description."""
    result = my_function()
    assert result == expected_value
```

### Integration Test Template
```python
# tests/test_orchestrator.py

@pytest.mark.integration
def test_full_workflow(temp_session):
    """Test description."""
    # Setup
    config = create_test_config(...)

    # Execute
    result = run_workflow(config)

    # Verify
    assert result.success
    assert (temp_session / "output.txt").exists()
```

### LLM Test Template
```python
@pytest.mark.requires_api_key
@pytest.mark.slow
def test_llm_feature(api_key):
    """Test description."""
    result = generate_with_llm(api_key)
    assert result is not None
```

## Troubleshooting

### "No module named 'pytest'"
```bash
pip install -r requirements-dev.txt
```

### "No API key available" (for LLM tests)
```bash
# Check if key is set
echo $TOGETHER_API_KEY

# Or check file
cat ~/together_api_key.txt

# Set it
export TOGETHER_API_KEY="your-key"
```

### Tests fail with import errors
```bash
# Ensure you're in the repo root
cd /path/to/sports_poetry_demo

# Run pytest from repo root
pytest
```

### Coverage report missing files
```bash
# Run from repo root with explicit source
pytest --cov=. --cov-report=html
```

## Current Test Status

As of the latest commit:

- ✅ **19 unit tests** - Template mode, word counting, error handling
- ✅ **2 integration tests** - Template workflow, logging
- ⏭️ **4 integration tests skipped** - Marked for future implementation
- ✅ **3 LLM tests** - Require API key (skipped if not available)

**Total: 19 passing, 4 skipped**

## Future Improvements

Tests marked with `@pytest.mark.skip` are planned for future implementation:

- Additional integration tests with proper config management
- Analyzer agent tests
- HuggingFace provider tests
- Retry logic tests
- Performance benchmarks

See Issue #5 for the full testing roadmap.

## Quick Reference

```bash
# Most common commands:

# Run all fast tests
pytest -m "not requires_api_key" -v

# Run with coverage
pytest --cov --cov-report=html

# Run specific test file
pytest tests/test_poetry_agent.py -v

# Run specific test
pytest tests/test_poetry_agent.py::test_generate_haiku_basketball

# Debug failing test
pytest tests/test_orchestrator.py::test_template_single_sport -v -s

# Parallel execution
pytest -n auto
```

---

**Questions?** See Issue #5 or run `pytest --help`
