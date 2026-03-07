"""Codebase exploration tools for Stage 0.

Defines 5 ToolDefinition objects that the agentic explore stage can call.
Each tool fetches data from the linked GitHub repository.
"""

import json
import logging

from app.providers.base import ToolDefinition
from app.services.github_service import get_repo_tree as _svc_get_repo_tree
from app.services.github_service import read_file_content as _svc_read_file_content

logger = logging.getLogger(__name__)


def build_codebase_tools(
    token: str,
    repo_full_name: str,
    repo_branch: str,
) -> list[ToolDefinition]:
    """Build the 5 codebase exploration tool definitions.

    Each tool handler is an async function that fetches data from GitHub.
    """

    # Shared tree cache to avoid re-fetching
    _tree_cache: dict[str, list[dict]] = {}

    async def _get_tree() -> list[dict]:
        if "tree" not in _tree_cache:
            try:
                # github_service already filters excluded files and applies size limits
                _tree_cache["tree"] = await _svc_get_repo_tree(token, repo_full_name, repo_branch)
            except Exception as e:
                logger.error(f"Failed to get repo tree: {e}")
                _tree_cache["tree"] = []
        return _tree_cache["tree"]

    # ---- Tool 1: list_repo_files ----
    async def list_repo_files_handler(args: dict) -> str:
        path_prefix = args.get("path_prefix", "")
        max_results = args.get("max_results", 200)

        tree = await _get_tree()
        filtered = tree
        if path_prefix:
            filtered = [e for e in tree if e["path"].startswith(path_prefix)]

        entries = filtered[:max_results]
        output = [{"path": e["path"], "size_bytes": e.get("size_bytes", 0)} for e in entries]
        return json.dumps(output, indent=2)

    list_repo_files = ToolDefinition(
        name="list_repo_files",
        description=(
            "List all files in the linked repository. Returns the complete file tree "
            "with paths, sizes, and SHA hashes. Call this first to understand "
            "the repository structure before reading specific files."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "path_prefix": {
                    "type": "string",
                    "description": "Filter to files under this path. Empty = all files.",
                },
                "max_results": {
                    "type": "integer",
                    "default": 200,
                    "description": "Max entries to return. Default 200.",
                },
            },
            "required": [],
        },
        handler=list_repo_files_handler,
    )

    # ---- Tool 2: read_file ----
    async def read_file_handler(args: dict) -> str:
        path = args.get("path", "")
        max_lines = args.get("max_lines", 200)

        if not path:
            return "Error: 'path' is required."

        tree = await _get_tree()
        entry = next((e for e in tree if e["path"] == path), None)
        if not entry:
            return f"Error: File '{path}' not found in repository."

        sha = entry.get("sha", "")
        if not sha:
            return f"Error: No SHA found for '{path}'."

        try:
            content = await _svc_read_file_content(token, repo_full_name, sha)
            if content is None:
                return f"Error: File '{path}' could not be read from repository."
            lines = content.split("\n")
            if len(lines) > max_lines:
                content = "\n".join(lines[:max_lines])
                content += f"\n\n... (truncated at {max_lines} lines, {len(lines)} total)"
            return content
        except Exception as e:
            return f"Error reading '{path}': {e}"

    read_file = ToolDefinition(
        name="read_file",
        description=(
            "Read the full content of a specific file from the linked repository. "
            "Use the exact path from list_repo_files. For large files (>50KB) "
            "only the first 200 lines are returned."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Exact file path as returned by list_repo_files",
                },
                "max_lines": {
                    "type": "integer",
                    "default": 200,
                },
            },
            "required": ["path"],
        },
        handler=read_file_handler,
    )

    # ---- Tool 3: search_code ----
    async def search_code_handler(args: dict) -> str:
        pattern = args.get("pattern", "")
        file_extension = args.get("file_extension", "")
        max_results = args.get("max_results", 30)

        if not pattern:
            return "Error: 'pattern' is required."

        tree = await _get_tree()
        if file_extension:
            ext = file_extension if file_extension.startswith(".") else f".{file_extension}"
            tree = [e for e in tree if e["path"].endswith(ext)]

        matches = []
        files_checked = 0
        for entry in tree[:20]:  # Max 20 files per search
            sha = entry.get("sha", "")
            if not sha:
                continue

            try:
                content = await _svc_read_file_content(token, repo_full_name, sha)
                if content is None:
                    continue
                files_checked += 1
                for i, line in enumerate(content.split("\n"), 1):
                    if pattern.lower() in line.lower():
                        matches.append(f"{entry['path']}:{i}: {line.strip()}")
                        if len(matches) >= max_results:
                            break
            except Exception:
                continue

            if len(matches) >= max_results:
                break

        if not matches:
            return f"No matches found for '{pattern}' (searched {files_checked} files)."

        return "\n".join(matches)

    search_code = ToolDefinition(
        name="search_code",
        description=(
            "Search for a text pattern across all files in the linked repository. "
            "Returns matching lines with file paths and line numbers. "
            "Use for finding API calls, imports, function definitions, etc."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Literal string or simple pattern to search for",
                },
                "file_extension": {
                    "type": "string",
                    "description": "Filter to files with this extension (e.g. 'py', 'ts', 'md'). Empty = all.",
                },
                "max_results": {
                    "type": "integer",
                    "default": 30,
                },
            },
            "required": ["pattern"],
        },
        handler=search_code_handler,
    )

    # ---- Tool 4: read_multiple_files ----
    async def read_multiple_files_handler(args: dict) -> str:
        paths = args.get("paths", [])
        if not paths:
            return "Error: 'paths' is required and must be a non-empty list."
        if len(paths) > 5:
            paths = paths[:5]

        tree = await _get_tree()
        tree_map = {e["path"]: e for e in tree}

        output_parts = []
        for path in paths:
            entry = tree_map.get(path)
            if not entry:
                output_parts.append(f"=== {path} ===\nError: File not found.\n")
                continue

            sha = entry.get("sha", "")
            if not sha:
                output_parts.append(f"=== {path} ===\nError: No SHA for file.\n")
                continue
            try:
                content = await _svc_read_file_content(token, repo_full_name, sha)
                if content is None:
                    output_parts.append(f"=== {path} ===\nError: File could not be read.\n")
                    continue
                lines = content.split("\n")
                if len(lines) > 150:
                    content = "\n".join(lines[:150])
                    content += "\n... (truncated at 150 lines)"
                output_parts.append(f"=== {path} ===\n{content}\n")
            except Exception as e:
                output_parts.append(f"=== {path} ===\nError: {e}\n")

        return "\n".join(output_parts)

    read_multiple_files = ToolDefinition(
        name="read_multiple_files",
        description=(
            "Read up to 5 files at once. More efficient than calling read_file multiple times. "
            "Returns each file separated by a clear header."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of file paths (max 5)",
                },
            },
            "required": ["paths"],
        },
        handler=read_multiple_files_handler,
    )

    # ---- Tool 5: get_repo_summary ----
    async def get_repo_summary_handler(args: dict) -> str:
        tree = await _get_tree()

        # Key files to look for
        summary_files = [
            "README.md", "README.rst", "README",
            "package.json", "pyproject.toml", "Cargo.toml",
            ".env.example", "CLAUDE.md",
        ]

        parts = []

        # Root directory listing
        root_entries = sorted(set(
            e["path"].split("/")[0] for e in tree
        ))
        parts.append(f"Repository: {repo_full_name} (branch: {repo_branch})")
        parts.append(f"Total files: {len(tree)}")
        parts.append("\nRoot directory:\n" + "\n".join(f"  {e}" for e in root_entries[:30]))

        # Fetch key files
        tree_map = {e["path"]: e for e in tree}
        total_lines = len("\n".join(parts).split("\n"))

        for fname in summary_files:
            if total_lines >= 300:
                break
            entry = tree_map.get(fname)
            if not entry:
                continue

            sha = entry.get("sha", "")
            if not sha:
                continue
            try:
                content = await _svc_read_file_content(token, repo_full_name, sha)
                if content is None:
                    continue
                lines = content.split("\n")
                max_lines = min(100, 300 - total_lines)
                if len(lines) > max_lines:
                    content = "\n".join(lines[:max_lines]) + "\n... (truncated)"
                parts.append(f"\n=== {fname} ===\n{content}")
                total_lines += len(content.split("\n"))
            except Exception:
                continue

        return "\n".join(parts)

    get_repo_summary = ToolDefinition(
        name="get_repo_summary",
        description=(
            "Get a high-level summary of the repository: README content, "
            "package/dependency files, and entry points. Always call this first "
            "to get oriented before exploring specific files."
        ),
        input_schema={
            "type": "object",
            "properties": {},
            "required": [],
        },
        handler=get_repo_summary_handler,
    )

    return [
        list_repo_files,
        read_file,
        search_code,
        read_multiple_files,
        get_repo_summary,
    ]
