# Setting Up Virtual Environment

For this project, it's best practice to use a virtual environment to isolate dependencies.

## Option 1: Using venv (Python standard)

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt

# When done, deactivate
deactivate
```

## Option 2: Using conda

```bash
# Create conda environment
conda create -n sports_poetry python=3.13

# Activate it
conda activate sports_poetry

# Install dependencies
pip install -r requirements-dev.txt

# When done, deactivate
conda deactivate
```

## Current Status

Currently using: **Base conda environment** (`/usr/licensed/anaconda3/2025.6/`)

To avoid polluting the base environment, create a project virtual environment first.

## Quick Check

```bash
# See which environment is active
which python

# See installed packages in current environment
pip list
```

## For API Testing

Once you have your virtual environment set up:

1. Install dependencies: `pip install -r requirements-dev.txt`
2. Set API key: `export ANTHROPIC_API_KEY="your-key-here"`
3. Run API tests: `pytest -m api -v`
