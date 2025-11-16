# Add E2E API Tests for create_config Skill

## Summary

Add comprehensive end-to-end API tests that validate the create_config skill's behavior using the Anthropic API. These tests will verify Claude's understanding and usage of the skill in realistic scenarios.

## Motivation

Currently, we have:
- ✅ Unit tests (11 tests) - Validate helper functions
- ✅ Integration tests (4 tests) - Validate workflow outputs
- ⚠️  API simulation tests (4 tests) - Basic Claude behavior validation
- ✅ Manual acceptance criteria - Documented test scenarios

**Gap**: The existing API tests are minimal and don't cover the complete skill workflow. We need comprehensive tests that validate:
1. Claude's end-to-end skill execution
2. Multi-turn conversation handling
3. Error recovery flows
4. Edge cases and validation scenarios

## Proposed Tests

### Test 1: Complete Happy Path (Template Mode)
**Scenario**: User requests template mode config creation
**Input**: "Create a config for hockey, swimming, volleyball"
**Expected**:
- Claude creates config file
- Claude creates generator script
- Files have correct structure
- Claude reports success with file paths

### Test 2: Complete LLM Mode Flow
**Scenario**: User requests LLM mode with API key present
**Input**: "Create an LLM mode config for cricket, rugby, golf"
**Expected**:
- Claude checks for API key
- Claude creates LLM mode config
- Config includes provider and model
- Generator script includes LLM settings

### Test 3: Validation Error Recovery
**Scenario**: User provides too few sports, then corrects
**Input**:
- Turn 1: "Create a config for tennis and golf"
- Turn 2: "Add baseball"
**Expected**:
- Claude catches validation error
- Claude explains the issue clearly
- Claude suggests adding more sports
- After correction, Claude creates valid config

### Test 4: Missing API Key Handling
**Scenario**: User requests LLM mode without API key
**Input**: "Create an LLM mode config for basketball, soccer, tennis"
**Expected** (with ANTHROPIC_API_KEY unset):
- Claude detects missing API key
- Claude provides setup instructions
- Claude offers template mode fallback
- No broken config created

### Test 5: Default Behavior Validation
**Scenario**: User provides minimal input
**Input**: "Create a config for basketball, soccer, tennis"
**Expected**:
- Claude uses template mode by default (doesn't ask)
- Claude enables retry by default (doesn't ask)
- Claude creates both files
- Process completes quickly (<5s)

## Acceptance Criteria

- [ ] All 5 new tests pass consistently
- [ ] Tests are marked with `@pytest.mark.api`
- [ ] Tests gracefully skip when `ANTHROPIC_API_KEY` not set
- [ ] Each test includes cost estimation in docstring
- [ ] Tests validate both Claude's responses AND file outputs
- [ ] Documentation updated with new test descriptions
- [ ] Tests run in <30 seconds total
- [ ] Total cost < $0.25 per full test run

## Implementation Notes

**Test organization**:
- Add to `tests/test_e2e_api_simulation.py` or create new file
- Use descriptive test names: `test_complete_happy_path_template_mode`
- Include detailed docstrings with expected behavior

**API usage optimization**:
- Use `claude-3-5-haiku-20241022` for most tests (~$0.001/test)
- Use `claude-sonnet-4-5-20250929` for critical path tests (~$0.01/test)
- Consider parameterized tests for model comparison

**Validation approach**:
- Check Claude's response content (natural language validation)
- Check actual file creation (filesystem validation)
- Check file structure (JSON/Python validation)
- Check execution flow (multi-turn conversation)

## Out of Scope

- Tool execution environment (complex, requires sandbox)
- Full multi-turn conversation with tool calls (requires Claude Code internals)
- Production monitoring/telemetry (separate feature)

## Related Work

- Existing tests: `tests/test_e2e_api_simulation.py`
- Documentation: `docs/E2E_TESTING_GUIDE.md`
- Manual acceptance criteria: `tests/test_create_config_skill.py` (docstrings)

## Estimated Effort

- Research/design: 30 minutes
- Implementation: 2-3 hours
- Testing/validation: 1 hour
- Documentation: 30 minutes

**Total**: ~4 hours

## Success Metrics

- Test coverage increases from 90% to 95%+ for skill behavior
- All manual acceptance criteria have corresponding automated tests
- API test suite runs before every release
- Zero false positives (tests pass when skill works correctly)
