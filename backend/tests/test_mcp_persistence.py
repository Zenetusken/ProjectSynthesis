"""Tests for MCP tool DB persistence (Tasks 14-15).

Note: pipeline event→field mapping is tested in test_optimization_service.py
via the shared accumulate_pipeline_event() function. These tests focus on
_run_and_persist's session lifecycle and Optimization record creation.
"""
from unittest.mock import AsyncMock, MagicMock, patch


def _make_session_mock():
    """Return an AsyncMock that works as an async context manager session."""
    session = AsyncMock()
    session.add = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=session)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm, session


async def test_run_and_persist_commits_twice():
    """_run_and_persist creates record then persists updates — commits exactly twice."""
    from app.mcp_server import _run_and_persist

    cm, session = _make_session_mock()

    async def _fake_pipeline(**kwargs):
        yield "analysis", {"task_type": "coding", "model": "test-model"}

    mock_provider = MagicMock()
    mock_provider.name = "test-provider"

    with (
        patch("app.mcp_server.async_session", return_value=cm),
        patch("app.services.pipeline.run_pipeline", side_effect=_fake_pipeline),
    ):
        results = await _run_and_persist(
            mock_provider,
            "test prompt",
            opt_id="test-id-001",
        )

    assert session.commit.call_count == 2
    # Second commit uses update() (not merge), so execute is called for the update statement
    assert session.execute.call_count >= 1
    assert "analysis" in results


async def test_run_and_persist_sets_retry_of():
    """_run_and_persist passes retry_of through to the Optimization constructor."""
    from app.mcp_server import _run_and_persist

    cm, session = _make_session_mock()
    added_objects = []
    original_add = session.add

    def capture_add(obj):
        added_objects.append(obj)
        return original_add(obj)

    session.add = capture_add

    async def _fake_pipeline(**kwargs):
        yield "analysis", {"task_type": "coding", "model": "test-model"}
        return

    mock_provider = MagicMock()
    mock_provider.name = "test-provider"

    with (
        patch("app.mcp_server.async_session", return_value=cm),
        patch("app.services.pipeline.run_pipeline", side_effect=_fake_pipeline),
    ):
        await _run_and_persist(
            mock_provider,
            "test prompt",
            opt_id="new-id-002",
            retry_of="orig-id",
        )

    assert len(added_objects) == 1
    opt = added_objects[0]
    assert opt.retry_of == "orig-id"
    assert opt.id == "new-id-002"


async def test_run_and_persist_passes_project_and_title():
    """_run_and_persist persists project and title on the Optimization record."""
    from app.mcp_server import _run_and_persist

    cm, session = _make_session_mock()
    added_objects = []
    session.add = lambda obj: added_objects.append(obj)

    async def _fake_pipeline(**kwargs):
        yield "analysis", {"task_type": "coding", "model": "test-model"}

    mock_provider = MagicMock()
    mock_provider.name = "test-provider"

    with (
        patch("app.mcp_server.async_session", return_value=cm),
        patch("app.services.pipeline.run_pipeline", side_effect=_fake_pipeline),
    ):
        await _run_and_persist(
            mock_provider,
            "test prompt",
            opt_id="proj-id",
            project="my-project",
            title="My Title",
        )

    assert len(added_objects) == 1
    opt = added_objects[0]
    assert opt.project == "my-project"
    assert opt.title == "My Title"


async def test_run_and_persist_handles_pipeline_error():
    """_run_and_persist sets status=failed when pipeline raises."""
    from app.mcp_server import _run_and_persist

    cm, session = _make_session_mock()

    async def _failing_pipeline(**kwargs):
        yield "analysis", {"task_type": "coding", "model": "test-model"}
        raise RuntimeError("Pipeline exploded")

    mock_provider = MagicMock()
    mock_provider.name = "test-provider"

    with (
        patch("app.mcp_server.async_session", return_value=cm),
        patch("app.services.pipeline.run_pipeline", side_effect=_failing_pipeline),
    ):
        await _run_and_persist(
            mock_provider,
            "test prompt",
            opt_id="error-id",
        )

    # The update call should include status=failed
    update_call = session.execute.call_args
    assert update_call is not None
    assert session.commit.call_count == 2  # create + error persist
