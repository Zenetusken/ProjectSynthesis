import warnings
from typing import Optional

from pydantic import BaseModel, Field

warnings.filterwarnings("ignore", message="Field name.*shadows an attribute")


class OptimizeRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="The raw prompt to optimize")
    project: Optional[str] = None
    tags: Optional[list[str]] = None
    title: Optional[str] = None
    strategy: Optional[str] = None
    repo_full_name: Optional[str] = None
    repo_branch: Optional[str] = None
    github_token: Optional[str] = None          # N23: non-browser clients
    file_contexts: Optional[list[dict]] = None  # N24: attached file content
    instructions: Optional[list[str]] = None    # N25: user output constraints
    url_contexts: Optional[list[str]] = None    # N26: URLs to fetch and inject


class PatchOptimizationRequest(BaseModel):
    title: Optional[str] = None
    tags: Optional[list[str]] = None
    version: Optional[str] = None
    project: Optional[str] = None


class RetryRequest(BaseModel):
    strategy: Optional[str] = None
    file_contexts: Optional[list[dict]] = None  # N32: forward file context on retry
    instructions: Optional[list[str]] = None    # N32: forward output constraints on retry
    url_contexts: Optional[list[str]] = None    # N32: forward URLs to fetch on retry
    github_token: Optional[str] = None          # N40: re-run Explore on retry


class HistoryStatsResponse(BaseModel):
    total_optimizations: int = 0
    average_score: Optional[float] = None
    task_type_breakdown: dict[str, int] = {}
    framework_breakdown: dict[str, int] = {}
    provider_breakdown: dict[str, int] = {}
    model_usage: dict[str, int] = {}
    codebase_aware_count: int = 0
    improvement_rate: Optional[float] = None
