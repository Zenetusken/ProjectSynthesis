"""Prompt diff utilities: hashing, cycle detection, dimension deltas.

Used by RetryOracle and pipeline diagnostics.
"""

import hashlib
import re

SCORE_DIMENSIONS = (
    "clarity_score",
    "specificity_score",
    "structure_score",
    "faithfulness_score",
    "conciseness_score",
)


def compute_prompt_hash(prompt: str) -> str:
    """Normalized hash for cycle detection. Case-insensitive, whitespace-collapsed."""
    normalized = re.sub(r"\s+", " ", prompt.strip().lower())
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def compute_dimension_deltas(
    before: dict[str, int | float],
    after: dict[str, int | float],
) -> dict[str, int | float]:
    """Compute per-dimension score changes between two validation results."""
    deltas: dict[str, int | float] = {}
    for dim in SCORE_DIMENSIONS:
        b = before.get(dim)
        a = after.get(dim)
        if b is not None and a is not None:
            deltas[dim] = a - b
    return deltas


def detect_cycle(
    current_hash: str,
    previous_hashes: list[str],
) -> int | None:
    """Check if current prompt hash matches any previous attempt.

    Returns 1-indexed attempt number of the match, or None if no cycle.
    """
    for i, h in enumerate(previous_hashes):
        if h == current_hash:
            return i + 1
    return None


def compute_prompt_entropy(prompt_a: str, prompt_b: str) -> float:
    """Jaccard similarity on sentence-level tokens.

    Returns 0.0 (identical) to 1.0 (completely different).
    Higher = more exploration.
    """
    def _sentences(text: str) -> set[str]:
        parts = re.split(r"[.!?\n]+", text.strip().lower())
        return {re.sub(r"\s+", " ", s.strip()) for s in parts if s.strip()}

    a_set = _sentences(prompt_a)
    b_set = _sentences(prompt_b)

    if not a_set and not b_set:
        return 0.0

    intersection = a_set & b_set
    union = a_set | b_set

    if not union:
        return 0.0

    similarity = len(intersection) / len(union)
    return round(1.0 - similarity, 4)
