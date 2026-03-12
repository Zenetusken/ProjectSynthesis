# Explore Intent-Adaptive Pipeline Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the explore stage prompt-intent-aware so it produces richer, behaviorally specific observations tailored to what the optimizer needs, then enhance context builders and optimizer consumption to leverage the richer output.

**Architecture:** Pre-explore Haiku intent classification drives adaptive observation directives into the synthesis prompt. Context builder caps are raised. Optimizer gets positive weaving guidance keyed by intent category. Six files modified, zero pipeline changes.

**Tech Stack:** Python 3.14, FastAPI, pytest, Haiku 4.5 (intent classification), existing LLMProvider abstraction

**Spec:** `docs/superpowers/specs/2026-03-12-explore-intent-adaptive-pipeline-design.md`

---

## Chunk 1: CodebaseContext Extension + Context Builder Enhancement

### Task 1: Extend CodebaseContext with intent_category and depth fields

**Files:**
- Modify: `backend/app/services/codebase_explorer.py:274-286`
- Test: `backend/tests/test_context_builders.py`

- [ ] **Step 1: Write failing tests for new fields**

Add to `backend/tests/test_context_builders.py` after the existing `test_codebase_context_asdict_complete_roundtrip` test (around line 208):

```python
def test_codebase_context_intent_category_default():
    """intent_category defaults to empty string."""
    ctx = CodebaseContext()
    assert ctx.intent_category == ""


def test_codebase_context_depth_default():
    """depth defaults to empty string."""
    ctx = CodebaseContext()
    assert ctx.depth == ""


def test_codebase_context_asdict_includes_intent_fields():
    """asdict() includes intent_category and depth."""
    ctx = CodebaseContext(intent_category="refactoring", depth="behavioral")
    d = asdict(ctx)
    assert d["intent_category"] == "refactoring"
    assert d["depth"] == "behavioral"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_context_builders.py::test_codebase_context_intent_category_default tests/test_context_builders.py::test_codebase_context_depth_default tests/test_context_builders.py::test_codebase_context_asdict_includes_intent_fields -v`
Expected: FAIL — `CodebaseContext` doesn't have `intent_category` or `depth` fields.

- [ ] **Step 3: Add fields to CodebaseContext**

In `backend/app/services/codebase_explorer.py`, modify the `CodebaseContext` dataclass (line 274-286). Add two fields after `explore_quality`:

```python
@dataclass
class CodebaseContext:
    repo: str = ""
    branch: str = "main"
    tech_stack: list[str] = field(default_factory=list)
    key_files_read: list[str] = field(default_factory=list)
    relevant_snippets: list[dict] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)
    grounding_notes: list[str] = field(default_factory=list)
    files_read_count: int = 0
    coverage_pct: int = 0
    duration_ms: int = 0
    explore_quality: str = "complete"
    intent_category: str = ""
    depth: str = ""
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_context_builders.py::test_codebase_context_intent_category_default tests/test_context_builders.py::test_codebase_context_depth_default tests/test_context_builders.py::test_codebase_context_asdict_includes_intent_fields -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/codebase_explorer.py backend/tests/test_context_builders.py
git commit -m "feat: add intent_category and depth fields to CodebaseContext"
```

---

### Task 2: Raise context builder caps and add intent header

**Files:**
- Modify: `backend/app/services/context_builders.py`
- Test: `backend/tests/test_context_builders.py`

- [ ] **Step 1: Write failing tests for new caps**

Add to `backend/tests/test_context_builders.py` — replace the existing cap tests with updated expectations. Add these new tests at the end:

```python
def test_codebase_observations_capped_at_12():
    """Observations cap raised from 8 to 12."""
    ctx = {"observations": [f"obs {i}" for i in range(16)]}
    result = build_codebase_summary(ctx)
    assert "obs 11" in result
    assert "obs 12" not in result


def test_codebase_grounding_notes_capped_at_12():
    """Grounding notes cap raised from 8 to 12."""
    ctx = {"grounding_notes": [f"note {i}" for i in range(16)]}
    result = build_codebase_summary(ctx)
    assert "note 11" in result
    assert "note 12" not in result


def test_codebase_snippets_capped_at_10():
    """Snippet count cap raised from 5 to 10."""
    ctx = {
        "relevant_snippets": [
            {"file": f"file{i}.py", "lines": "1-5", "context": f"code {i}"}
            for i in range(14)
        ]
    }
    result = build_codebase_summary(ctx)
    assert "file9.py" in result
    assert "file10.py" not in result


def test_codebase_snippet_content_capped_at_1200_chars():
    """Snippet content cap raised from 600 to 1200 chars."""
    long_content = "x" * 1400
    ctx = {
        "relevant_snippets": [
            {"file": "big.py", "lines": "1-100", "context": long_content}
        ]
    }
    result = build_codebase_summary(ctx)
    assert "x" * 1200 in result
    assert "x" * 1201 not in result


def test_codebase_key_files_capped_at_20():
    """Key files cap raised from 10 to 20."""
    ctx = {"key_files_read": [f"file{i}.py" for i in range(25)]}
    result = build_codebase_summary(ctx)
    assert "file19.py" in result
    assert "file20.py" not in result


def test_codebase_tech_stack_capped_at_15():
    """Tech stack cap raised from 10 to 15."""
    ctx = {"tech_stack": [f"lang{i}" for i in range(20)]}
    result = build_codebase_summary(ctx)
    assert "lang14" in result
    assert "lang15" not in result


def test_codebase_intent_header_shown_for_non_general():
    """Intent header appears when intent_category is set and not 'general'."""
    ctx = {"intent_category": "refactoring", "depth": "behavioral", "repo": "o/r", "branch": "main"}
    result = build_codebase_summary(ctx)
    assert "Intent focus: refactoring (depth: behavioral)" in result


def test_codebase_intent_header_omitted_for_general():
    """Intent header is omitted when intent_category is 'general'."""
    ctx = {"intent_category": "general", "repo": "o/r", "branch": "main"}
    result = build_codebase_summary(ctx)
    assert "Intent focus" not in result


def test_codebase_intent_header_omitted_when_absent():
    """Intent header is omitted when intent_category is empty/absent."""
    ctx = {"repo": "o/r", "branch": "main"}
    result = build_codebase_summary(ctx)
    assert "Intent focus" not in result


def test_codebase_intent_header_no_depth_when_empty():
    """Intent header omits depth qualifier when depth is empty."""
    ctx = {"intent_category": "testing", "depth": "", "repo": "o/r", "branch": "main"}
    result = build_codebase_summary(ctx)
    assert "Intent focus: testing" in result
    assert "(depth:" not in result
```

- [ ] **Step 2: Run new tests to verify they fail**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_context_builders.py::test_codebase_observations_capped_at_12 tests/test_context_builders.py::test_codebase_snippets_capped_at_10 tests/test_context_builders.py::test_codebase_snippet_content_capped_at_1200_chars tests/test_context_builders.py::test_codebase_key_files_capped_at_20 tests/test_context_builders.py::test_codebase_tech_stack_capped_at_15 tests/test_context_builders.py::test_codebase_intent_header_shown_for_non_general -v`
Expected: FAIL — caps are still at old values, intent header doesn't exist.

- [ ] **Step 3: Update context_builders.py**

In `backend/app/services/context_builders.py`, make these changes:

**a)** Update the docstring (line 37) to reflect new caps.

**b)** Change cap values in `build_codebase_summary()`:
- Line 85: `tech_stack[:10]` → `tech_stack[:15]`
- Line 89: `key_files[:10]` → `key_files[:20]`
- Line 94: `list(observations)[:8]` → `list(observations)[:12]`
- Line 100: `list(grounding_notes)[:8]` → `list(grounding_notes)[:12]`
- Line 106: `snippets[:5]` → `snippets[:10]`
- Line 109: `[:600]` → `[:1200]`

**c)** Add intent header after the repo/branch block (after line 75, before the `files_read_count` check):

```python
    intent = codebase_context.get("intent_category")
    depth = codebase_context.get("depth", "")
    if intent and intent != "general":
        parts.append(f"Intent focus: {intent}" + (f" (depth: {depth})" if depth else ""))
```

- [ ] **Step 4: Update old tests that check old cap values**

In `backend/tests/test_context_builders.py`:

Delete these five tests (replaced by the new cap tests above):
- `test_codebase_snippets_capped_at_5` (line 310)
- `test_codebase_snippet_content_capped_at_600_chars` (line 324)
- `test_codebase_observations_capped_at_8` (line 337)
- `test_codebase_grounding_notes_capped_at_8` (line 345)
- `test_codebase_tech_stack_capped_at_10` (line 353)

- [ ] **Step 5: Run all context_builders tests**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_context_builders.py -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/context_builders.py backend/tests/test_context_builders.py
git commit -m "feat: raise context builder caps and add intent header"
```

---

### Task 3: Raise validator codebase summary truncation cap

**Files:**
- Modify: `backend/app/services/validator.py:115`

- [ ] **Step 1: Change truncation cap**

In `backend/app/services/validator.py`, line 115, change:
```python
                f"{codebase_summary[:2500]}"
```
to:
```python
                f"{codebase_summary[:4000]}"
```

- [ ] **Step 2: Run existing validator tests**

Run: `cd backend && source .venv/bin/activate && pytest tests/ -k validator -v`
Expected: PASS (no tests check this specific cap value)

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/validator.py
git commit -m "feat: raise validator codebase summary cap from 2500 to 4000 chars"
```

---

## Chunk 2: Intent Classification + Explore Synthesis Enhancement

### Task 4: Add intent classification schema and function

**Files:**
- Modify: `backend/app/services/codebase_explorer.py`
- Test: `backend/tests/test_explore_phase.py`

- [ ] **Step 1: Write failing tests for intent classification**

Add `import asyncio` to the imports at the top of `backend/tests/test_explore_phase.py` (after line 3, alongside the existing imports). Then add these imports and test class at the end of the file:

```python
from app.services.codebase_explorer import (
    INTENT_CLASSIFICATION_SCHEMA,
    _classify_prompt_intent,
)


class TestIntentClassification:
    """Tests for the pre-explore intent classification microstep."""

    def test_schema_has_required_fields(self):
        """INTENT_CLASSIFICATION_SCHEMA requires all four output fields."""
        assert set(INTENT_CLASSIFICATION_SCHEMA["required"]) == {
            "intent_category", "observation_directives", "snippet_priorities", "depth"
        }

    def test_schema_intent_category_is_enum(self):
        """intent_category is constrained to known categories."""
        enum_vals = INTENT_CLASSIFICATION_SCHEMA["properties"]["intent_category"]["enum"]
        assert "refactoring" in enum_vals
        assert "general" in enum_vals
        assert "api_design" in enum_vals
        assert len(enum_vals) == 11

    def test_schema_depth_is_enum(self):
        """depth is constrained to structural/behavioral/relational."""
        enum_vals = INTENT_CLASSIFICATION_SCHEMA["properties"]["depth"]["enum"]
        assert set(enum_vals) == {"structural", "behavioral", "relational"}

    @pytest.mark.asyncio
    async def test_returns_default_on_provider_failure(self):
        """On provider error, returns general/structural fallback."""
        provider = AsyncMock()
        provider.complete_json = AsyncMock(side_effect=Exception("API error"))
        result = await _classify_prompt_intent(provider, "some prompt")
        assert result["intent_category"] == "general"
        assert result["depth"] == "structural"
        assert result["observation_directives"] == []
        assert result["snippet_priorities"] == []

    @pytest.mark.asyncio
    async def test_returns_default_on_timeout(self):
        """On timeout, returns general/structural fallback."""
        async def slow_call(**kwargs):
            await asyncio.sleep(20)
            return {}

        provider = AsyncMock()
        provider.complete_json = slow_call
        result = await _classify_prompt_intent(provider, "some prompt", timeout_seconds=0.1)
        assert result["intent_category"] == "general"

    @pytest.mark.asyncio
    async def test_passes_schema_to_provider(self):
        """Verifies complete_json is called with the schema parameter."""
        provider = AsyncMock()
        provider.complete_json = AsyncMock(return_value={
            "intent_category": "refactoring",
            "observation_directives": ["find smells"],
            "snippet_priorities": ["complex functions"],
            "depth": "behavioral",
        })
        result = await _classify_prompt_intent(provider, "refactor this code")
        provider.complete_json.assert_called_once()
        call_kwargs = provider.complete_json.call_args.kwargs
        assert call_kwargs["schema"] is INTENT_CLASSIFICATION_SCHEMA
        assert result["intent_category"] == "refactoring"

    @pytest.mark.asyncio
    async def test_returns_parsed_result_on_success(self):
        """Successful classification returns the parsed dict."""
        expected = {
            "intent_category": "testing",
            "observation_directives": ["find test patterns", "check coverage"],
            "snippet_priorities": ["test files"],
            "depth": "behavioral",
        }
        provider = AsyncMock()
        provider.complete_json = AsyncMock(return_value=expected)
        result = await _classify_prompt_intent(provider, "write tests for auth")
        assert result == expected
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_explore_phase.py::TestIntentClassification -v`
Expected: FAIL — `INTENT_CLASSIFICATION_SCHEMA` and `_classify_prompt_intent` don't exist.

- [ ] **Step 3: Implement INTENT_CLASSIFICATION_SCHEMA and _classify_prompt_intent**

In `backend/app/services/codebase_explorer.py`, add after the `EXPLORE_OUTPUT_SCHEMA` definition (after line 271, before the `CodebaseContext` dataclass):

```python
# ── Intent classification schema ──────────────────────────────────────
# Used by _classify_prompt_intent() to classify the user's prompt intent
# before synthesis, so the explore model can adapt its observations.

INTENT_CLASSIFICATION_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "intent_category": {
            "type": "string",
            "enum": [
                "refactoring", "api_design", "feature_build", "testing",
                "debugging", "architecture_review", "performance",
                "documentation", "migration", "security", "general",
            ],
        },
        "observation_directives": {
            "type": "array",
            "items": {"type": "string"},
            "description": "2-4 specific instructions for what the explore model should focus on",
        },
        "snippet_priorities": {
            "type": "array",
            "items": {"type": "string"},
            "description": "2-3 types of code regions to prioritize in snippet extraction",
        },
        "depth": {
            "type": "string",
            "enum": ["structural", "behavioral", "relational"],
            "description": "Observation depth preference",
        },
    },
    "required": ["intent_category", "observation_directives", "snippet_priorities", "depth"],
}

_INTENT_DEFAULT: dict = {
    "intent_category": "general",
    "depth": "structural",
    "observation_directives": [],
    "snippet_priorities": [],
}

_INTENT_SYSTEM_PROMPT = """\
You are a prompt intent classifier for a codebase exploration system.

Given a user's prompt, classify what KIND of codebase intelligence a downstream
prompt optimizer will need to write a surgically precise optimized version.

Your classification drives what the codebase explorer focuses on:
- "structural" depth: module layout, file organization, component locations
- "behavioral" depth: function behaviors, hardcoded values, conditional branches, side effects
- "relational" depth: dependencies, data flow, integration points, contracts between modules

Intent categories and their typical focus:
- refactoring: code smells, cross-cutting concerns, hardcoded values, duplication, behavioral patterns
- api_design: endpoint structure, request/response shapes, middleware chain, data contracts
- feature_build: module layout, extension points, existing patterns to follow, conventions
- testing: test coverage signals, testability barriers, mock patterns, fixture setup
- debugging: error paths, state mutations, side effects, exception handling patterns
- architecture_review: dependency graph, layer violations, coupling points, module boundaries
- performance: hot paths, caching patterns, I/O boundaries, concurrency primitives
- documentation: public APIs, module purposes, data flow overview, configuration surface
- migration: dependencies, integration boundaries, version-specific patterns
- security: auth flows, input validation, credential handling, encryption patterns
- general: module layout, key abstractions, data flow patterns (use when no specific intent)

Observation directives tell the explorer WHAT to look for. Be specific:
  Good: "Identify behavioral patterns with specific values (hardcoded constants, magic numbers)"
  Bad: "Look at the code structure"

Snippet priorities tell the explorer WHICH code regions to extract:
  Good: "Functions with conditional branching or multiple code paths"
  Bad: "Important functions"

Your response must be a JSON object matching the required schema."""


async def _classify_prompt_intent(
    provider: "LLMProvider",
    raw_prompt: str,
    model: str = "claude-haiku-4-5",
    timeout_seconds: float = 8.0,
) -> dict:
    """Classify the user's prompt intent for adaptive explore synthesis.

    Returns a dict with intent_category, observation_directives,
    snippet_priorities, and depth. On any failure, returns the default
    (general/structural) — this is a best-effort enhancement, not a gate.
    """
    try:
        result = await asyncio.wait_for(
            provider.complete_json(
                system=_INTENT_SYSTEM_PROMPT,
                user=raw_prompt,
                model=model,
                schema=INTENT_CLASSIFICATION_SCHEMA,
            ),
            timeout=timeout_seconds,
        )
        # Validate required fields are present
        if not isinstance(result, dict) or "intent_category" not in result:
            logger.warning("Intent classification returned invalid result, using default")
            return dict(_INTENT_DEFAULT)
        return result
    except asyncio.TimeoutError:
        logger.warning("Intent classification timed out after %.1fs", timeout_seconds)
        return dict(_INTENT_DEFAULT)
    except Exception as e:
        logger.warning("Intent classification failed: %s", e)
        return dict(_INTENT_DEFAULT)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_explore_phase.py::TestIntentClassification -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/codebase_explorer.py backend/tests/test_explore_phase.py
git commit -m "feat: add intent classification schema and function for explore stage"
```

---

### Task 5: Enhance the explore synthesis prompt

**Files:**
- Modify: `backend/app/prompts/explore_synthesis_prompt.py`

- [ ] **Step 1: Rewrite the synthesis prompt**

Replace the entire content of `backend/app/prompts/explore_synthesis_prompt.py` with the enhanced version. Key changes from the spec:

```python
"""Stage 0: Codebase Explore — single-shot synthesis prompt.

Replaces the multi-turn agentic explore prompt. Used after the semantic
index has pre-selected and batch-read the most relevant files. The model
receives all file contents in one shot and synthesizes a CodebaseContext.

The explore phase is the INTELLIGENCE AND CONTEXT LAYER — it provides
navigational intelligence (where things are, how they connect, what
patterns are used) so that a downstream executor can act with precision.
It does NOT perform the task requested in the user's prompt.
"""


def get_explore_synthesis_prompt() -> str:
    """System prompt for single-shot codebase synthesis.

    The model receives pre-assembled file contents (selected by embedding
    similarity + deterministic anchors) and must produce structured output
    matching EXPLORE_OUTPUT_SCHEMA — no tool calls, no multi-turn.

    IMPORTANT: This prompt must produce INTELLIGENCE (navigational context
    for a downstream executor) — NOT execution-layer output (auditing,
    bug-finding, correctness verification). The explore phase tells the
    executor WHERE to look and WHAT to expect, not what is right or wrong.
    """
    return """\
You are a codebase intelligence assistant for Project Synthesis.

You have been given a set of pre-selected files from a GitHub repository. These files
were chosen by semantic relevance to the user's prompt, plus key anchor files (README,
manifests, config).

## Your role — INTELLIGENCE LAYER, not execution layer

Your job is to provide NAVIGATIONAL INTELLIGENCE — context that helps a downstream
executor understand the codebase architecture so they can carry out the user's prompt
with precision. You are the reconnaissance phase, not the action phase.

You MUST NOT:
- Perform the task the user's prompt is requesting (e.g., don't audit code quality,
  don't find bugs, don't evaluate correctness, don't assess whether implementations
  are "proper" or "improper")
- Make judgments about whether code is correct, broken, incomplete, or missing
- Flag things as "not implemented", "not called", "missing", or "wrong"
- Diagnose bugs or suggest fixes
- Evaluate business logic correctness

You MUST:
- Map the architecture: what components exist, where they live, how they connect
- Identify the relevant files and code regions the executor should examine
- Describe data flow patterns, handoff mechanisms, and structural relationships
- Surface the conventions, patterns, and abstractions the codebase uses
- Provide enough structural context that an executor can navigate precisely

Think of yourself as a guide who knows the terrain, not an inspector who judges the buildings.

## Your task

Analyze ALL provided files and produce a structured JSON response with these fields:

### tech_stack (required)
List every technology, framework, library, and language you can identify from the files.
Include version numbers when visible in manifests. Be specific:
  - Good: ["Python 3.12", "FastAPI 0.115", "SQLAlchemy 2.x (async)", "Redis", "SvelteKit 2"]
  - Bad: ["Python", "web framework", "database"]

### key_files_read (required)
List every file path you were given. These are already the most relevant files.

### relevant_code_snippets (optional but valuable)
Extract 5–12 code snippets that are structurally relevant to the user's prompt intent,
prioritized by the snippet priorities directive if provided:
  - Each snippet: {"file": "path/to/file.py", "lines": "45-62", "context": "behavioral \
description of what this code does"}
  - Line numbers are shown in the provided file content (format: "   N | code"). Use ONLY \
the line numbers visible in the numbered output. Never estimate or extrapolate line numbers \
beyond what is shown.
  - Prioritize: entry points, key interfaces, data structures, handoff points, and the \
specific code regions the prompt's intent relates to
  - Describe WHAT the code does behaviorally, not just structurally. Include specific \
values, branch conditions, and behavioral characteristics. \
Bad: "stream method for CLI provider". \
Good: "stream() method: text blocks converted to word-boundary chunks via hardcoded \
CHUNK_TARGET=60 and 3ms inter-chunk sleep. Simulated streaming differs from \
AnthropicAPIProvider.stream() which uses SDK text_stream."

### codebase_observations (required)
8–12 key observations about architecture, patterns, and structure, adapted to the \
observation directives provided:
  - Project layout and module organization
  - Key architectural patterns (layering, dependency direction, service boundaries)
  - Data flow: how information moves between components
  - Framework conventions and idioms used
  - Integration points: where components connect or hand off to each other
Each observation must be specific, reference actual file paths, and describe
STRUCTURE — not correctness.

For every observation, be microscopically specific. Include function/method names, \
variable names, hardcoded values, and line ranges where visible. Do not write \
"the provider uses conditional logic" — write "AnthropicAPIProvider._make_extra() \
(anthropic_api.py:55-77) branches on _THINKING_MODELS membership and schema \
presence, producing three output paths: adaptive thinking, JSON output_config, \
or plain completion."

When the observation directives indicate behavioral or relational depth, trace \
patterns ACROSS module boundaries. If you see the same concern handled differently \
in multiple files (e.g., caching, error handling, configuration), describe each \
instance with specific function names and contrast the approaches.

### prompt_grounding_notes (required)
This is the MOST IMPORTANT field. Provide context intelligence that helps an executor
carry out the user's prompt with precision:
  - Map the prompt's intent to specific codebase locations: "The pipeline stages the \
prompt refers to are defined in X, Y, Z files"
  - Identify the key abstractions and interfaces relevant to the prompt's goal
  - Note the data shapes and handoff mechanisms the executor will encounter
  - Surface architectural context that would otherwise require exploration: "Stage \
outputs flow via SSE tuples from pipeline.py; each stage yields (event_type, event_data)"
  - When files are truncated, note what is visible vs. what lies beyond visible range
  - If the provided files don't cover something the prompt's intent relates to, note \
what files/areas are NOT covered so the executor knows to look there independently

When the observation directives specify behavioral depth, grounding notes should \
include execution-level detail that an optimizer can weave directly into a prompt: \
specific function signatures, parameter types, return shapes, and concrete values. \
The optimizer will use these to write surgically precise instructions — give it \
the ammunition.

Quality standard:
  GOOD: "The pipeline stages referenced by the prompt are orchestrated in pipeline.py \
via run_pipeline(). Each stage (explore, analyze, strategy, optimize, validate) is a \
separate service in services/. Handoffs use AsyncGenerator yielding (event_type, event_data) \
tuples. The executor should examine each stage's run_* function for the data contract."
  GOOD: "The auth flow spans three files: github_auth.py (OAuth router), github_service.py \
(token encryption), and github_client.py (API calls with decrypted tokens). Token resolution \
happens in github_client._get_decrypted_token()."
  BAD: "The auth middleware is missing proper validation" (this is an execution-layer judgment)
  BAD: "Function X is NOT called anywhere" (this is bug diagnosis, not navigation)
  BAD: "The pipeline has inconsistent error handling" (this is an audit finding)

### Quantitative metadata
When visible in the codebase, note quantitative signals in your observations or \
grounding notes: test file count vs source file count (proxy for coverage), number of \
TODO/FIXME comments, number of configuration sources, dependency count. These help \
downstream stages calibrate effort estimates and constraint severity.

## Rules
- Do NOT hallucinate file paths or function names. Only reference what you can see.
- Do NOT fabricate line numbers. If a file is truncated, state that explicitly.
- Do NOT evaluate correctness, find bugs, or make quality judgments — that is the \
executor's job, not yours.
- Do NOT perform the task described in the user's prompt — provide the intelligence \
needed to perform it.
- Be concise but precise. Every observation must be grounded in actual file content.
- Your ENTIRE response must be a single valid JSON object. Do not include ANY text, \
commentary, or explanation before or after the JSON. Do not use markdown code fences. \
The very first character of your response must be `{` and the very last must be `}`.
"""
```

- [ ] **Step 2: Run existing explore tests to verify nothing breaks**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_explore_phase.py -v`
Expected: ALL PASS (prompt is consumed as a string — no structural dependencies)

- [ ] **Step 3: Commit**

```bash
git add backend/app/prompts/explore_synthesis_prompt.py
git commit -m "feat: enhance explore synthesis prompt with specificity and cross-cutting guidance"
```

---

### Task 6: Wire intent classification into run_explore()

**Files:**
- Modify: `backend/app/services/codebase_explorer.py:783-814`

- [ ] **Step 1: Add intent classification call and directive injection**

In `backend/app/services/codebase_explorer.py`, **replace lines 783-814 exactly** (from the `# ── Phase 3:` comment through the closing parenthesis of `user_message = (...)`). Lines 816+ (the `try: parsed = await asyncio.wait_for(...)` block) remain untouched.

The replacement adds a new Phase 2.5 before the existing Phase 3 content, and modifies the user_message construction to include directives:

Replace lines 783-814 with:

```python
    # ── Phase 2.5: Intent classification ──────────────────────────────
    intent = await _classify_prompt_intent(provider, raw_prompt)

    yield ("tool_call", {
        "tool": "intent_classification",
        "input": {"prompt_length": len(raw_prompt)},
        "output": {"intent": intent["intent_category"], "depth": intent.get("depth", "")},
        "status": "complete",
    })

    # ── Phase 3: Single-shot LLM synthesis ────────────────────────────
    yield ("agent_text", {"content": "Synthesizing codebase analysis..."})
    yield ("tool_call", {
        "tool": "llm_synthesis",
        "input": {"model": model, "files": len(file_contents)},
        "status": "running",
    })

    system_prompt = get_explore_synthesis_prompt()
    # Runtime char guard — prevent context overflow on repos with long lines
    context_payload = _format_files_for_llm(file_contents)
    max_context_chars = settings.EXPLORE_MAX_CONTEXT_CHARS
    if len(context_payload) > max_context_chars:
        logger.warning(
            "Explore context exceeds %d chars (%d chars); trimming semantic files",
            max_context_chars, len(context_payload),
        )
        # Remove semantic-tier files (last in priority) until within budget
        # Note: this also affects key_files_read downstream (intentional —
        # trimmed files were not shown to the LLM)
        paths_by_priority = list(file_contents.keys())
        while len(context_payload) > max_context_chars and paths_by_priority:
            removed = paths_by_priority.pop()
            del file_contents[removed]
            context_payload = _format_files_for_llm(file_contents)

    # Build directive section from intent classification
    directive_section = ""
    if intent.get("observation_directives") or intent.get("snippet_priorities"):
        parts = [
            "\nObservation directives (adapt your analysis accordingly):",
            f"  Intent: {intent.get('intent_category', 'general')}",
            f"  Depth: {intent.get('depth', 'structural')}",
        ]
        if intent.get("observation_directives"):
            parts.append("  Focus areas:")
            for d in intent["observation_directives"]:
                parts.append(f"    - {d}")
        if intent.get("snippet_priorities"):
            parts.append("  Snippet priorities:")
            for p in intent["snippet_priorities"]:
                parts.append(f"    - {p}")
        directive_section = "\n".join(parts) + "\n"

    user_message = (
        f"User's prompt to optimize:\n---\n{raw_prompt}\n---\n"
        f"{directive_section}\n"
        f"Repository: {repo_full_name} (branch: {used_branch})\n"
        f"Total files in repo: {total_in_tree}\n"
        f"Files provided below: {len(file_contents)}\n\n"
        f"{context_payload}"
    )
```

- [ ] **Step 2: Set intent fields on CodebaseContext**

In the same file, after the CodebaseContext construction (line 869-881), add the intent fields. After `explore_quality="complete" if parsed else "partial",` add:

```python
        intent_category=intent["intent_category"],
        depth=intent.get("depth", ""),
```

- [ ] **Step 3: Run all explore tests**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_explore_phase.py tests/test_context_builders.py -v`
Expected: ALL PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/codebase_explorer.py
git commit -m "feat: wire intent classification into run_explore with directive injection"
```

---

## Chunk 3: Optimizer Enhancement

### Task 7: Add weaving guidance dict and restructure optimizer context injection

**Files:**
- Modify: `backend/app/services/optimizer.py`

- [ ] **Step 1: Add _WEAVING_GUIDANCE dict**

In `backend/app/services/optimizer.py`, add after the imports (near the top of the file, after the existing constants):

```python
# ── Intent-specific weaving guidance ──────────────────────────────────
# Maps explore intent_category to positive instructions telling the
# optimizer HOW to integrate codebase intelligence into the final prompt.
_WEAVING_GUIDANCE: dict[str, str] = {
    "refactoring": (
        "- Construct a prioritized Scope section mapping observations to specific files/functions\n"
        "- Use coverage % and test file counts to calibrate effort estimates\n"
        "- Extract architectural constraints from project docs and make them explicit"
    ),
    "api_design": (
        "- Use endpoint observations to define the API surface\n"
        "- Reference data contracts and integration points as explicit interface requirements"
    ),
    "feature_build": (
        "- Reference existing patterns the executor should follow\n"
        "- Name extension points and module boundaries"
    ),
    "testing": (
        "- Use coverage signals and testability observations to scope what needs testing\n"
        "- Reference mock patterns and test infrastructure"
    ),
    "debugging": (
        "- Map error paths and state mutations into a structured investigation plan\n"
        "- Reference specific functions and their behavioral characteristics"
    ),
    "architecture_review": (
        "- Use dependency and coupling observations to define review dimensions\n"
        "- Reference layer violations and cross-cutting concerns as explicit review criteria"
    ),
    "performance": (
        "- Reference hot paths, I/O boundaries, and caching patterns as profiling targets"
    ),
    "security": (
        "- Map auth flows and credential handling into explicit review scope\n"
        "- Reference input validation patterns and encryption usage"
    ),
}
_DEFAULT_WEAVING = (
    "- Use file paths, function names, and data shapes to make instructions precise\n"
    "- Let codebase specifics inform the precision of your instructions"
)
```

- [ ] **Step 2: Replace the codebase context injection block**

In the same file, replace the current codebase context injection (the `if codebase_context:` block around lines 156-176) with:

```python
    if codebase_context:
        codebase_summary = build_codebase_summary(codebase_context)
        if codebase_summary:
            intent_cat = codebase_context.get("intent_category", "general")
            coverage = codebase_context.get("coverage_pct", 0)
            files_read = codebase_context.get("files_read_count", 0)
            weaving = _WEAVING_GUIDANCE.get(intent_cat, _DEFAULT_WEAVING)

            user_message += (
                "\n\n--- Codebase reference (INTELLIGENCE LAYER — for YOUR understanding only) ---\n"
                f"Intent focus: {intent_cat} · Coverage: {coverage}% · {files_read} files\n\n"
                "Weaving guidance (how to USE this context in the optimized prompt):\n"
                f"{weaving}\n\n"
                "Guardrails:\n"
                "- Do NOT relay exploration findings, observations, or context notes\n"
                "- Do NOT add 'Codebase Context' or 'Background' sections\n"
                "- Do NOT treat observations marked [unverified] as fact\n"
                "- Do NOT delegate investigation tasks to the executor\n"
                "- Do NOT invent specifics beyond what appears below\n\n"
                f"{codebase_summary}\n"
                "--- End codebase reference ---"
            )
```

- [ ] **Step 3: Run existing optimizer tests**

Run: `cd backend && source .venv/bin/activate && pytest tests/ -k optimize -v`
Expected: ALL PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/optimizer.py
git commit -m "feat: add intent-specific weaving guidance to optimizer context injection"
```

---

### Task 8: Add codebase-aware paragraphs to optimizer prompts

**Files:**
- Modify: `backend/app/prompts/optimizer_prompts.py`

- [ ] **Step 1: Append codebase-aware paragraphs to task-type additions**

In `backend/app/prompts/optimizer_prompts.py`, append to the relevant `_TASK_SPECIFIC_ADDITIONS` entries:

**coding** (after line 68, before the closing `"""`):
```python
- When codebase context is available, construct a prioritized Scope section that maps
  observations to ordered priorities with specific file paths and function names. Use
  quantitative metrics (coverage %, file counts) to calibrate effort levels in any
  estimation guidance. Extract layer rules or architectural constraints from observations
  and make them explicit constraints the executor must respect.
```

**analysis** (after line 77, before the closing `"""`):
```python
- When codebase context is available, use architectural observations to define analysis
  dimensions. Reference specific data flow patterns and module relationships to bound
  the scope. Turn cross-cutting observations into explicit review criteria.
```

**reasoning** (after line 86, before the closing `"""`):
```python
- When codebase context is available, reference specific functions, data structures, and
  module relationships to make reasoning steps concrete. Use architectural observations
  to frame the reasoning scope.
```

**general** (after line 173, before the closing `"""`):
```python
- When codebase context is available, use file paths, function names, and data shapes
  to make instructions precise wherever the observations provide specifics.
```

**other** (after line 181, before the closing `"""`):
```python
- When codebase context is available, use file paths, function names, and data shapes
  to make instructions precise wherever the observations provide specifics.
```

- [ ] **Step 2: Run existing tests**

Run: `cd backend && source .venv/bin/activate && pytest tests/ -k optimize -v`
Expected: ALL PASS

- [ ] **Step 3: Commit**

```bash
git add backend/app/prompts/optimizer_prompts.py
git commit -m "feat: add codebase-aware guidance to task-type optimizer prompts"
```

---

## Chunk 4: Full Integration Verification

### Task 9: Run full test suite and verify backward compatibility

**Files:**
- No new files

- [ ] **Step 1: Run the complete backend test suite**

Run: `cd backend && source .venv/bin/activate && pytest tests/ -v --tb=short`
Expected: ALL PASS — no regressions from any of the changes.

- [ ] **Step 2: Verify the explore phase test imports work**

Run: `cd backend && source .venv/bin/activate && python -c "from app.services.codebase_explorer import CodebaseContext, INTENT_CLASSIFICATION_SCHEMA, _classify_prompt_intent; print('imports OK')"`
Expected: `imports OK`

- [ ] **Step 3: Verify context builders work with new and old data**

Run: `cd backend && source .venv/bin/activate && python -c "
from app.services.context_builders import build_codebase_summary
# Old-style data (no intent fields) — must still work
old = {'repo': 'o/r', 'branch': 'main', 'observations': ['obs1'], 'tech_stack': ['Python']}
print('Old format:', bool(build_codebase_summary(old)))
# New-style data (with intent fields)
new = {**old, 'intent_category': 'refactoring', 'depth': 'behavioral'}
result = build_codebase_summary(new)
print('New format has intent:', 'Intent focus' in result)
print('OK')
"`
Expected: Old format: True, New format has intent: True, OK

- [ ] **Step 4: Update CHANGELOG.md**

Add to the `## Unreleased` section:

```
- Added pre-explore intent classification to adapt codebase observations to prompt intent
- Improved explore synthesis prompt with behavioral specificity and cross-cutting guidance
- Changed context builder caps: observations 8→12, grounding notes 8→12, snippets 5→10, snippet content 600→1200 chars, key files 10→20, tech stack 10→15
- Added intent-specific weaving guidance to optimizer codebase context injection
- Added codebase-aware paragraphs to coding, analysis, reasoning, and general optimizer prompts
- Changed validator codebase summary cap from 2500 to 4000 chars
```

- [ ] **Step 5: Final commit**

```bash
git add CHANGELOG.md
git commit -m "docs: update CHANGELOG with explore intent-adaptive pipeline changes"
```
