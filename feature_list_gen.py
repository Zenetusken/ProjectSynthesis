"""
Feature list batch generator — pre-copied to project_dir by the orchestrator.
The initializer agent writes tier batches (batch_t0.json, batch_t1.json, …),
then calls merge() to produce feature_list_1.json and feature_list_2.json.
"""
import json
from pathlib import Path

_ROOT = Path(__file__).parent

_VALID_TIERS = ("T0", "T1", "T2", "T3", "T4", "T5")
_TIER_ORDER = {tier: i for i, tier in enumerate(_VALID_TIERS)}


def t(tier, cat, title, desc, steps, depends=None, setup=None, outcome=None):
    """Create one test entry (id assigned by merge).

    Args:
        tier:    One of T0–T5.
        cat:     Feature domain label (e.g. "auth", "crud", "ui-layout").
        title:   Short human-readable name (≤80 chars).
        desc:    What the feature IS and what constitutes success.
        steps:   Non-empty list of Puppeteer-action-verb step strings.
        depends: Optional list of test IDs that must pass first.
        setup:   Optional list of precondition strings.
        outcome: One-sentence success description (defaults to title).
    """
    if tier not in _VALID_TIERS:
        raise ValueError(f"Invalid tier {tier!r} — must be one of {_VALID_TIERS}")
    if not title or not title.strip():
        raise ValueError("title must be a non-empty string")
    if not steps:
        raise ValueError(f"steps must be a non-empty list (test: {title!r})")
    return {
        "tier": tier,
        "category": cat,
        "title": title,
        "description": desc,
        "depends_on": depends or [],
        "setup": setup or [
            "Backend running (see server_state in scratchpad for URL)",
            "Frontend running (see server_state in scratchpad for URL)",
        ],
        "steps": steps,
        "expected_outcome": outcome or title,
        "passes": False,
    }


def save_batch(name: str, tests: list) -> None:
    """Write a list of test dicts to batch_<name>.json.

    Args:
        name:  Batch name suffix (e.g. "t0", "t1a"). File will be batch_<name>.json.
        tests: Non-empty list of test dicts produced by t().
    """
    if not tests:
        raise ValueError(f"save_batch('{name}'): tests list is empty")
    out = _ROOT / f"batch_{name}.json"
    out.write_text(json.dumps(tests, indent=2), encoding="utf-8")
    print(f"  [fl_gen] saved {out.name}: {len(tests)} tests")


def merge(large_spec: bool = False) -> None:
    """Merge all batch_*.json files → feature_list_*.json with sequential IDs.

    Collects all batch files, sorts tests by tier (T0→T5), assigns sequential
    IDs starting at 1, writes output files, then removes the batch files.

    Args:
        large_spec: If True, split into 3 files by tier group (T0+T1 / T2+T3 / T4+T5).
                    Use for specs over 7,500 lines. Default: 2-file even split.
    """
    batch_files = sorted(_ROOT.glob("batch_*.json"))
    if not batch_files:
        raise FileNotFoundError("No batch_*.json files found — run the tier scripts first")

    tests = []
    for bf in batch_files:
        chunk = json.loads(bf.read_text(encoding="utf-8"))
        if not isinstance(chunk, list):
            raise ValueError(f"{bf.name}: expected a JSON array, got {type(chunk).__name__}")
        tests.extend(chunk)

    if len(tests) < 300:
        raise ValueError(
            f"Only {len(tests)} tests merged — a full build requires 300+. "
            "Check that all tier batch scripts ran successfully."
        )

    # Sort by tier order (T0 → T5) to guarantee correct ID assignment regardless
    # of batch file naming or creation order.
    tests.sort(key=lambda x: _TIER_ORDER.get(x.get("tier", ""), 99))

    # Assign sequential IDs
    for i, entry in enumerate(tests):
        entry["id"] = i + 1

    n = len(tests)

    if not large_spec:
        mid = n // 2
        (_ROOT / "feature_list_1.json").write_text(
            json.dumps(tests[:mid], indent=2), encoding="utf-8"
        )
        (_ROOT / "feature_list_2.json").write_text(
            json.dumps(tests[mid:], indent=2), encoding="utf-8"
        )
        print(f"[fl_gen] feature_list_1.json: {mid} tests")
        print(f"[fl_gen] feature_list_2.json: {n - mid} tests")
    else:
        t0t1 = [x for x in tests if x["tier"] in ("T0", "T1")]
        t2t3 = [x for x in tests if x["tier"] in ("T2", "T3")]
        t4t5 = [x for x in tests if x["tier"] in ("T4", "T5")]
        if not t0t1:
            raise ValueError("large_spec merge: no T0/T1 tests found — check batch files")
        if not t2t3:
            raise ValueError("large_spec merge: no T2/T3 tests found — check batch files")
        if not t4t5:
            print("[fl_gen] WARNING: no T4/T5 tests — skipping feature_list_3.json")
        (_ROOT / "feature_list_1.json").write_text(
            json.dumps(t0t1, indent=2), encoding="utf-8"
        )
        (_ROOT / "feature_list_2.json").write_text(
            json.dumps(t2t3, indent=2), encoding="utf-8"
        )
        print(f"[fl_gen] feature_list_1.json: {len(t0t1)} tests (T0+T1)")
        print(f"[fl_gen] feature_list_2.json: {len(t2t3)} tests (T2+T3)")
        if t4t5:
            (_ROOT / "feature_list_3.json").write_text(
                json.dumps(t4t5, indent=2), encoding="utf-8"
            )
            print(f"[fl_gen] feature_list_3.json: {len(t4t5)} tests (T4+T5)")

    print(f"[fl_gen] Total: {n} tests")

    # Clean up batch files
    for bf in batch_files:
        bf.unlink()
    print("[fl_gen] Cleaned up batch files")


def verify() -> None:
    """Print counts per file and tier; warn if below 300 tests."""
    files = sorted(_ROOT.glob("feature_list_*.json"))
    if not files:
        print("[fl_gen] ERROR: No feature_list_*.json found!")
        return
    all_tests = []
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        all_tests.extend(data)
        tiers: dict[str, int] = {}
        for entry in data:
            key = entry.get("tier", "?")
            tiers[key] = tiers.get(key, 0) + 1
        tier_str = " | ".join(f"{k}:{v}" for k, v in sorted(tiers.items()))
        print(f"  {f.name}: {len(data)} tests  [{tier_str}]")
    print(f"  TOTAL: {len(all_tests)} tests across {len(files)} files")
    if len(all_tests) < 300:
        print(f"  WARNING: only {len(all_tests)} tests — need 300+")


if __name__ == "__main__":
    verify()
