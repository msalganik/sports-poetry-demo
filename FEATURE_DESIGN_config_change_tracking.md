# Feature Design: Default Config with Change Tracking

**Status**: Planning Phase
**Created**: 2025-11-02
**Goal**: Create a default config.json file and only update the parts that change, with full change tracking

---

## Current State Analysis

**Current behavior:**
- `ConfigBuilder.__init__()` sets defaults (config_builder.py:31-39)
- Every config creation starts fresh or overwrites existing files
- No tracking of what changed between configs
- No concept of a "default" config file

**Current defaults (hardcoded in ConfigBuilder):**
```python
{
    "sports": [],
    "session_id": None,
    "timestamp": None,
    "retry_enabled": True,
    "generation_mode": "template",
    "llm_provider": "together",
    "llm_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
}
```

---

## Proposed Feature Design (SIMPLIFIED)

### Core Principles
1. **Always start from default** - No loading existing config, no merging
2. **Fail fast** - If `config.default.json` doesn't exist, stop immediately
3. **Per-session changelogs** - One changelog per session, stored in session directory
4. **Track what matters** - Only track meaningful field changes (exclude auto-generated fields)
5. **Explicit attribution** - Always track who made the change

### 1. Default Config File Structure

Create `config.default.json` in the repository root (checked into git):

```json
{
  "sports": ["basketball", "soccer", "tennis"],
  "session_id": null,
  "timestamp": null,
  "retry_enabled": true,
  "generation_mode": "template",
  "llm_provider": "together",
  "llm_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
}
```

**Key decisions:**
- **No `_metadata` field** - Flat structure, no nested objects to complicate diffs
- **Must exist** - Code fails immediately if missing (no fallback logic)
- **Default sports included** - Provides working example format

**File management:**
- `config.default.json` - Checked into git, must exist (FAIL if missing)
- `config.json` - Current/active config (gitignored)
- `output/{session_id}/config.changelog.json` - Per-session changelog (single JSON file, not JSONL)

### 2. Simplified API

Add ONE new method to `ConfigBuilder` class:

```python
class ConfigBuilder:

    @staticmethod
    def load_default(path: str = "config.default.json") -> 'ConfigBuilder':
        """
        Load the default configuration template.

        Raises:
            FileNotFoundError: If config.default.json doesn't exist
            ConfigValidationError: If default config is invalid
        """
        if not Path(path).exists():
            raise FileNotFoundError(
                f"Default config not found: {path}\n"
                f"Repository may be corrupted. This file must exist."
            )
        return ConfigBuilder.load(path)

    def save_with_changelog(self,
                           config_path: str = "config.json",
                           reason: str,
                           user: str = "unknown") -> Path:
        """
        Save config and write changelog to session directory.

        Args:
            config_path: Where to save config (default: config.json)
            reason: Required explanation of what changed and why
            user: Who made the change (e.g., "claude_code", "cli", "api")

        Returns:
            Path to saved config file

        Side effects:
            - Writes config to config_path
            - Creates output/{session_id}/ directory
            - Writes output/{session_id}/config.changelog.json
        """
        pass
```

**That's it!** No merge, no load_or_default, no separate diff method.

**Usage pattern (always the same):**

```python
# Every config creation follows this pattern:
builder = ConfigBuilder.load_default()  # FAIL if missing
builder.with_sports(["hockey", "swimming", "volleyball"])
builder.with_generation_mode("llm")  # If different from default
builder.save_with_changelog(
    reason="User changed sports and enabled LLM mode",
    user="claude_code"
)
```

### 3. Final Simplified Changelog Format

Location: `output/{session_id}/config.changelog.json` (single JSON file per session)

**Record structure - combines human readability with machine auditability:**

```json
{
  "timestamp": "2025-11-01T18:40:00Z",
  "session_id": "session_20251101_184000",
  "user": "claude_code",
  "reason": "User changed sports and enabled LLM mode",
  "changed_from_default": ["sports", "generation_mode"],
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

**Field descriptions:**
- `timestamp` - When changelog was created (ISO 8601)
- `session_id` - Which session this is for
- `user` - Who made the change ("claude_code", "cli", "api", etc.)
- `reason` - Required explanation (no optional reasons)
- `changed_from_default` - Quick summary array (human-readable scan)
- `changes` - Full old/new values (machine-auditable details)

**Key design decision:**
- Compare against `config.default.json` only (not previous config.json)
- "old" = value from default template
- "new" = value in current config
- Simpler: one baseline comparison, not tracking run-to-run changes

**What gets tracked in `changes`:**
- ✅ `sports` - User-specified sports list
- ✅ `generation_mode` - Template vs LLM
- ✅ `llm_provider` - Together vs HuggingFace
- ✅ `llm_model` - Model identifier
- ✅ `retry_enabled` - Retry behavior

**What does NOT get tracked:**
- ❌ `session_id` - Always changes, not meaningful
- ❌ `timestamp` - Always changes, not meaningful
- ❌ No `unchanged_fields` - Can be inferred
- ❌ No `diff_summary` - Can count keys in `changes`

**Example 1: Using all defaults**

```json
{
  "timestamp": "2025-11-01T18:35:00Z",
  "session_id": "session_20251101_183500",
  "user": "claude_code",
  "reason": "Initial configuration using all defaults",
  "changed_from_default": [],
  "changes": {}
}
```

Note: Empty arrays mean all values came from default unchanged.

**Example 2: Changed sports only**

```json
{
  "timestamp": "2025-11-01T18:40:00Z",
  "session_id": "session_20251101_184000",
  "user": "claude_code",
  "reason": "User changed sports selection",
  "changed_from_default": ["sports"],
  "changes": {
    "sports": {
      "old": ["basketball", "soccer", "tennis"],
      "new": ["hockey", "swimming", "volleyball"]
    }
  }
}
```

**Example 3: Multiple changes**

```json
{
  "timestamp": "2025-11-01T18:45:00Z",
  "session_id": "session_20251101_184500",
  "user": "cli",
  "reason": "User requested LLM mode with custom model",
  "changed_from_default": ["sports", "generation_mode", "llm_model"],
  "changes": {
    "sports": {
      "old": ["basketball", "soccer", "tennis"],
      "new": ["tennis", "golf", "swimming"]
    },
    "generation_mode": {
      "old": "template",
      "new": "llm"
    },
    "llm_model": {
      "old": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
      "new": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo-Free"
    }
  }
}
```

**Viewing changelogs:**

```bash
# View changelog for specific session
cat output/session_20251101_184000/config.changelog.json | jq .

# Quick scan: What changed from default?
cat output/session_20251101_184000/config.changelog.json | jq .changed_from_default

# View all session changelogs
find output -name "config.changelog.json" -exec cat {} \; | jq -s .

# Find sessions where sports changed
find output -name "config.changelog.json" -exec jq 'select(.changed_from_default | contains(["sports"]))' {} \;

# Summary of all changes across sessions
find output -name "config.changelog.json" -exec jq '{session: .session_id, changed: .changed_from_default, user: .user, reason: .reason}' {} \;

# Machine audit: Get exact old/new values for sports changes
find output -name "config.changelog.json" -exec jq 'select(.changes.sports) | {session: .session_id, sports: .changes.sports}' {} \;
```

### 4. Final Simplified Change Tracking Logic

**On save_with_changelog():**

```python
def save_with_changelog(self, config_path="config.json", reason=None, user="unknown"):
    # 1. Build and validate new config
    new_config = self.build()  # Includes session_id, timestamp

    # 2. Load default config (always compare against this baseline)
    default_config = ConfigBuilder.load("config.default.json").config

    # 3. Compute diff vs default (exclude auto-generated fields)
    changed_from_default, changes = compute_changes_from_default(default_config, new_config)

    # 4. Save new config
    with open(config_path, 'w') as f:
        json.dump(new_config, f, indent=2)

    # 5. Write changelog to session directory
    session_id = new_config["session_id"]
    session_dir = Path(f"output/{session_id}")
    session_dir.mkdir(parents=True, exist_ok=True)

    changelog = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "session_id": session_id,
        "user": user,
        "reason": reason,
        "changed_from_default": changed_from_default,
        "changes": changes
    }

    changelog_path = session_dir / "config.changelog.json"
    with open(changelog_path, 'w') as f:
        json.dump(changelog, f, indent=2)

    return Path(config_path)

def compute_changes_from_default(default_config, new_config):
    """
    Compare new config against default template.

    Returns:
        tuple: (changed_field_names, detailed_changes_dict)
    """
    EXCLUDE_FIELDS = {"session_id", "timestamp"}

    changed_fields = []
    changes = {}

    for key in new_config:
        if key in EXCLUDE_FIELDS:
            continue

        default_value = default_config.get(key)
        new_value = new_config[key]

        if default_value != new_value:
            changed_fields.append(key)
            changes[key] = {
                "old": default_value,
                "new": new_value
            }

    return changed_fields, changes
```

**Key simplifications:**
- Compare against default only (one baseline, not previous run)
- Return both summary list and detailed dict
- Flat config (no nested objects)
- Excludes session_id and timestamp from changes
- Empty arrays if using all defaults

**Edge cases handled:**
- ✅ All defaults used (changed_from_default=[], changes={})
- ✅ Session directory doesn't exist (creates it)
- ✅ Default config must exist (will fail if missing - intentional)

### 5. Integration with Claude Code Skill

**Simplified approach:**
- Always start from `config.default.json`
- Show user the defaults
- Ask what they want to change
- Apply changes and save with changelog

**Updated conversation flow:**

```
User: "Create a config for hockey, swimming, volleyball"

Claude: I'll create a configuration starting from defaults:

        Default settings:
        • Sports: basketball, soccer, tennis
        • Mode: template
        • Provider: together
        • Model: meta-llama/Llama-3.3-70B-Instruct-Turbo-Free
        • Retry: enabled

        You specified different sports. Keep other defaults? [yes/no]

User: "yes"

Claude: ✓ Created config.json

        Applied changes:
        • sports: basketball, soccer, tennis → hockey, swimming, volleyball

        Kept defaults:
        • generation_mode: template
        • llm_provider: together
        • llm_model: meta-llama/Llama-3.3-70B-Instruct-Turbo-Free
        • retry_enabled: true

        Changelog: output/session_20251101_184000/config.changelog.json
        Session ID: session_20251101_184000

        Ready to run: python3 orchestrator.py
```

**Code Claude executes:**

```python
from config_builder import ConfigBuilder

builder = ConfigBuilder.load_default()
builder.with_sports(["hockey", "swimming", "volleyball"])
builder.save_with_changelog(
    reason="User specified sports: hockey, swimming, volleyball",
    user="claude_code"
)
```

### 6. Simplified Testing Strategy

**Unit tests needed:**

```python
# test_config_builder.py additions

def test_load_default_exists():
    """Load default config successfully."""

def test_load_default_missing():
    """Fail with clear error if default missing."""

def test_save_with_changelog_first_config():
    """First config creation (action=create, changes={})."""

def test_save_with_changelog_update_sports():
    """Update existing config, track sports change."""

def test_save_with_changelog_multiple_changes():
    """Track multiple field changes."""

def test_save_with_changelog_no_changes():
    """Re-save identical config (changes={})."""

def test_changelog_excludes_auto_fields():
    """Verify session_id and timestamp not in changes."""

def test_changelog_location():
    """Verify changelog written to output/{session_id}/."""

def test_changelog_required_fields():
    """Verify all required fields present in changelog."""
```

**Integration tests:**
- Create config → run orchestrator → verify changelog exists in session dir
- Sequential configs → verify each has its own changelog

---

## Design Decisions Made

### ✅ Simplifications Applied

1. **Always start from default** - No merge, no load_or_default complexity
2. **Fail fast on missing default** - Clear error, no fallback logic
3. **Flat config structure** - No nested `_metadata` field
4. **Compare vs default only** - Not tracking run-to-run changes, just diff from baseline
5. **Dual-level tracking** - `changed_from_default` array (quick scan) + `changes` dict (full audit)
6. **Per-session changelogs** - One JSON file per session (not global JSONL)
7. **Exclude auto-fields** - Don't track session_id/timestamp changes
8. **Required reason** - Every change must be explained
9. **Track user attribution** - Keep "user" field to track Claude vs CLI

### ✅ What We Kept

- **`user` field** - Important for tracking what Claude is doing
- **Old/new values** - Full change detail for machine auditability
- **Quick summary** - `changed_from_default` array for human readability
- **Backward compatibility** - Keep existing `save()`, add `save_with_changelog()`

### ✅ What We Removed

- ~~`action` field~~ - Can infer from context
- ~~`unchanged_fields`~~ - Can be inferred (all fields not in changed_from_default)
- ~~`diff_summary`~~ - Can count changed_from_default.length
- ~~Tracking vs previous run~~ - Only compare vs default baseline
- ~~`load_or_default()` method~~ - Always use load_default()
- ~~`merge_from_file()` method~~ - Not needed with "always from default" approach

### ✅ Implementation Scope

**In scope:**
- `load_default()` class method
- `save_with_changelog(reason, user)` instance method
- `config.default.json` template (checked into git)
- Per-session changelog files
- Unit tests for new functionality

**Out of scope (for now):**
- Rollback functionality
- Changelog aggregation tools
- CLI commands for viewing history
- Validation migration tools

---

## Simplified Implementation Plan

**Phase 1: Core functionality** (2-3 hours)
1. Create `config.default.json` with default values
2. Add `ConfigBuilder.load_default()` class method
3. Add `ConfigBuilder.save_with_changelog(reason, user)` instance method
4. Add `compute_meaningful_changes()` helper function

**Phase 2: Testing** (1-2 hours)
5. Write 8-10 unit tests for new methods
6. Write 2 integration tests
7. Verify existing tests still pass

**Phase 3: Documentation** (1 hour)
8. Update `.claude/skills/create_config.md` for new flow
9. Update `CLAUDE.md` with changelog examples
10. Add `config.default.json` to README

**Total estimate: 4-6 hours of development**

**Files to modify:**
- `config_builder.py` - Add 2 methods (~50 lines)
- `tests/test_config_builder.py` - Add tests (~150 lines)
- `.claude/skills/create_config.md` - Update skill instructions
- `CLAUDE.md` - Update docs

**Files to create:**
- `config.default.json` - Default template (~15 lines)

---

## Related Files

**To modify:**
- `config_builder.py` - Add `load_default()` and `save_with_changelog()`
- `tests/test_config_builder.py` - Add new unit tests
- `.claude/skills/create_config.md` - Update skill for new flow
- `CLAUDE.md` - Document changelog feature

**To create:**
- `config.default.json` - Default config template (checked into git)

**Generated at runtime:**
- `config.json` - Active config (gitignored, in root)
- `output/{session_id}/config.changelog.json` - Per-session changelog (in session dir)

---

## Summary

This simplified design provides:
- ✅ Default config file (must exist)
- ✅ Change tracking vs default baseline (not run-to-run)
- ✅ Dual-level visibility (quick scan + full audit)
- ✅ Per-session audit trail
- ✅ Clear attribution (who changed what and why)
- ✅ Minimal complexity (2 new methods, ~50 lines of code)

**Key principles:**
1. Always start from default
2. Compare against one stable baseline (not previous runs)
3. Provide both human-readable summary and machine-auditable details
4. Keep it simple
