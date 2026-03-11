"""Tests for optimization_service CRUD functions."""
import json
from unittest.mock import AsyncMock, MagicMock


async def test_update_optimization_encodes_secondary_frameworks():
    """update_optimization must JSON-encode secondary_frameworks list, not store repr."""
    mock_opt = MagicMock()
    mock_opt.id = "test-id"
    mock_opt.secondary_frameworks = None
    mock_opt.to_dict.return_value = {"secondary_frameworks": ["CO-STAR", "RISEN"]}

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_opt
    mock_session.execute.return_value = mock_result

    from app.services.optimization_service import update_optimization
    await update_optimization(mock_session, "test-id", secondary_frameworks=["CO-STAR", "RISEN"])

    assert mock_opt.secondary_frameworks == json.dumps(["CO-STAR", "RISEN"])


def test_valid_sort_columns_exported():
    from app.services.optimization_service import VALID_SORT_COLUMNS
    assert "created_at" in VALID_SORT_COLUMNS
    assert "overall_score" in VALID_SORT_COLUMNS
    assert "status" in VALID_SORT_COLUMNS
    assert "primary_framework" in VALID_SORT_COLUMNS
    assert "raw_prompt" not in VALID_SORT_COLUMNS


async def test_compute_stats_empty_db(tmp_path):
    """compute_stats returns zero-state dict when no optimizations exist."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    import app.models.optimization  # noqa
    from app.database import Base

    eng = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/stats.db")
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        from app.services.optimization_service import compute_stats
        result = await compute_stats(session)

    assert result["total_optimizations"] == 0
    assert result["average_score"] is None
    assert result["task_type_breakdown"] == {}
    assert result["framework_breakdown"] == {}
    assert result["provider_breakdown"] == {}
    assert result["model_usage"] == {}
    assert result["codebase_aware_count"] == 0
    assert result["improvement_rate"] is None
    await eng.dispose()


async def test_compute_stats_respects_project_filter(tmp_path):
    """compute_stats must not raise when project filter is provided."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    import app.models.optimization  # noqa
    from app.database import Base

    eng = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/stats2.db")
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        from app.services.optimization_service import compute_stats
        result = await compute_stats(session, project="my-project")

    assert result["total_optimizations"] == 0
    assert result["framework_breakdown"] == {}
    assert result["provider_breakdown"] == {}
    assert result["model_usage"] == {}
    assert result["codebase_aware_count"] == 0
    assert result["improvement_rate"] is None
    await eng.dispose()


async def test_list_optimizations_with_user_id_filter(tmp_path):
    """list_optimizations must filter by user_id when provided."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    import app.models.optimization  # noqa: F401
    from app.database import Base
    from app.models.optimization import Optimization
    from app.services.optimization_service import list_optimizations

    eng = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/list_user.db")
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)

    # Seed two records with different user_ids
    async with Session() as session:
        session.add(Optimization(id="opt-a", raw_prompt="prompt a", user_id="user-1", status="completed"))
        session.add(Optimization(id="opt-b", raw_prompt="prompt b", user_id="user-2", status="completed"))
        await session.commit()

    async with Session() as session:
        items, total = await list_optimizations(session, user_id="user-1")

    assert total == 1
    assert items[0]["id"] == "opt-a"
    await eng.dispose()


def test_accumulate_pipeline_event_analysis():
    """accumulate_pipeline_event returns correct dict for analysis events."""
    from app.services.optimization_service import accumulate_pipeline_event

    result = accumulate_pipeline_event("analysis", {
        "task_type": "coding",
        "complexity": "medium",
        "weaknesses": ["vague"],
        "strengths": ["clear goal"],
        "model": "haiku",
        "analysis_quality": "full",
    })
    assert result["task_type"] == "coding"
    assert result["complexity"] == "medium"
    assert result["weaknesses"] == json.dumps(["vague"])
    assert result["strengths"] == json.dumps(["clear goal"])
    assert result["model_analyze"] == "haiku"
    assert result["analysis_quality"] == "full"


def test_accumulate_pipeline_event_validation_extracts_scores():
    """accumulate_pipeline_event unpacks scores sub-dict for validation events."""
    from app.services.optimization_service import accumulate_pipeline_event

    result = accumulate_pipeline_event("validation", {
        "scores": {"clarity_score": 8, "overall_score": 7},
        "is_improvement": True,
        "verdict": "improved",
        "issues": ["minor"],
        "model": "sonnet",
        "validation_quality": "full",
    })
    assert result["clarity_score"] == 8
    assert result["overall_score"] == 7
    assert result["is_improvement"] is True
    assert result["issues"] == json.dumps(["minor"])
    assert result["model_validate"] == "sonnet"


def test_accumulate_pipeline_event_unknown_type_returns_empty():
    """accumulate_pipeline_event returns empty dict for unrecognized event types."""
    from app.services.optimization_service import accumulate_pipeline_event

    assert accumulate_pipeline_event("unknown_event", {"data": 1}) == {}
    assert accumulate_pipeline_event("stage", {"status": "complete"}) == {}


def test_accumulate_pipeline_event_strategy_maps_rationale_key():
    """accumulate_pipeline_event maps event_data 'rationale' to 'strategy_rationale' column."""
    from app.services.optimization_service import accumulate_pipeline_event

    result = accumulate_pipeline_event("strategy", {
        "primary_framework": "CO-STAR",
        "secondary_frameworks": ["RISEN"],
        "rationale": "Best fit for coding tasks",
        "strategy_source": "llm",
        "model": "haiku",
    })
    assert result["primary_framework"] == "CO-STAR"
    assert result["strategy_rationale"] == "Best fit for coding tasks"
    assert result["secondary_frameworks"] == json.dumps(["RISEN"])
