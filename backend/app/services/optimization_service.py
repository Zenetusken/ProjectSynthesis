"""Optimization CRUD service.

Provides async database operations for creating, listing, retrieving,
and deleting optimization records via SQLAlchemy async sessions.
"""

import json
import logging
from typing import Optional

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.optimization import Optimization

logger = logging.getLogger(__name__)


async def create_optimization(
    session: AsyncSession,
    *,
    raw_prompt: str,
    title: Optional[str] = None,
    project: Optional[str] = None,
    tags: Optional[list[str]] = None,
    repo_full_name: Optional[str] = None,
    repo_branch: Optional[str] = None,
) -> Optimization:
    """Create a new optimization record in pending state.

    Args:
        session: Async database session.
        raw_prompt: The raw prompt text to optimize.
        title: Optional title for the optimization.
        project: Optional project grouping key.
        tags: Optional list of tag strings.
        repo_full_name: Optional linked GitHub repo (owner/repo).
        repo_branch: Optional branch name for the linked repo.

    Returns:
        The newly created Optimization ORM instance.
    """
    optimization = Optimization(
        raw_prompt=raw_prompt,
        title=title,
        project=project,
        tags=json.dumps(tags) if tags else "[]",
        linked_repo_full_name=repo_full_name,
        linked_repo_branch=repo_branch,
        status="pending",
    )
    session.add(optimization)
    await session.flush()
    await session.refresh(optimization)
    logger.info("Created optimization %s (status=pending)", optimization.id)
    return optimization


async def list_optimizations(
    session: AsyncSession,
    *,
    limit: int = 50,
    offset: int = 0,
    project: Optional[str] = None,
    task_type: Optional[str] = None,
    search: Optional[str] = None,
    sort: str = "created_at",
    order: str = "desc",
) -> tuple[list[dict], int]:
    """List optimizations with pagination, filtering, and sorting.

    Args:
        session: Async database session.
        limit: Maximum number of results to return.
        offset: Number of results to skip.
        project: Filter by project name.
        task_type: Filter by task type classification.
        search: Search term to match against raw_prompt and title.
        sort: Column name to sort by.
        order: Sort direction ('asc' or 'desc').

    Returns:
        Tuple of (list of optimization dicts, total count).
    """
    query = select(Optimization)
    count_query = select(func.count(Optimization.id))

    if project:
        query = query.where(Optimization.project == project)
        count_query = count_query.where(Optimization.project == project)

    if task_type:
        query = query.where(Optimization.task_type == task_type)
        count_query = count_query.where(Optimization.task_type == task_type)

    if search:
        search_pattern = f"%{search}%"
        search_filter = (
            Optimization.raw_prompt.ilike(search_pattern)
            | Optimization.title.ilike(search_pattern)
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    # Sorting
    sort_column = getattr(Optimization, sort, Optimization.created_at)
    if order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    query = query.limit(limit).offset(offset)

    result = await session.execute(query)
    optimizations = result.scalars().all()

    count_result = await session.execute(count_query)
    total = count_result.scalar() or 0

    return [opt.to_dict() for opt in optimizations], total


async def get_optimization(
    session: AsyncSession,
    optimization_id: str,
) -> Optional[dict]:
    """Get a single optimization by ID.

    Args:
        session: Async database session.
        optimization_id: The UUID of the optimization to retrieve.

    Returns:
        Optimization dict if found, None otherwise.
    """
    result = await session.execute(
        select(Optimization).where(Optimization.id == optimization_id)
    )
    opt = result.scalar_one_or_none()
    if opt is None:
        return None
    return opt.to_dict()


async def get_optimization_orm(
    session: AsyncSession,
    optimization_id: str,
) -> Optional[Optimization]:
    """Get a single optimization ORM object by ID.

    Args:
        session: Async database session.
        optimization_id: The UUID of the optimization to retrieve.

    Returns:
        Optimization ORM instance if found, None otherwise.
    """
    result = await session.execute(
        select(Optimization).where(Optimization.id == optimization_id)
    )
    return result.scalar_one_or_none()


async def update_optimization(
    session: AsyncSession,
    optimization_id: str,
    **kwargs,
) -> Optional[dict]:
    """Update fields on an existing optimization.

    Args:
        session: Async database session.
        optimization_id: The UUID of the optimization to update.
        **kwargs: Fields to update (column_name=value pairs).

    Returns:
        Updated optimization dict if found, None otherwise.
    """
    opt = await get_optimization_orm(session, optimization_id)
    if opt is None:
        return None

    for key, value in kwargs.items():
        if hasattr(opt, key):
            # JSON-encode list fields
            if key in ("weaknesses", "strengths", "changes_made", "issues", "tags"):
                if isinstance(value, list):
                    value = json.dumps(value)
            setattr(opt, key, value)

    await session.flush()
    await session.refresh(opt)
    return opt.to_dict()


async def delete_optimization(
    session: AsyncSession,
    optimization_id: str,
) -> bool:
    """Delete an optimization by ID.

    Args:
        session: Async database session.
        optimization_id: The UUID of the optimization to delete.

    Returns:
        True if deleted, False if not found.
    """
    opt = await get_optimization_orm(session, optimization_id)
    if opt is None:
        return False

    await session.delete(opt)
    await session.flush()
    logger.info("Deleted optimization %s", optimization_id)
    return True
