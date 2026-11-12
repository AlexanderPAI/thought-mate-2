from fnmatch import fnmatchcase
from pathlib import Path

from src.main_agent.config.config import agent_config

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _resolve_workspace_path(workspace: str, path: str) -> Path:
    """Resolve a relative path and verify it stays within the workspace."""
    directory = agent_config.workspaces.get(workspace)
    if directory is None:
        raise ValueError(f"Unknown workspace: {workspace!r}")

    relative_path = Path(path)
    if relative_path.is_absolute():
        raise ValueError("Path must be relative to the workspace root")

    root = (PROJECT_ROOT / directory).resolve()
    file_path = (root / relative_path).resolve()

    if not file_path.is_relative_to(root):
        raise ValueError("Path is outside the workspace root")

    return file_path


def read_file(workspace: str, path: str) -> str:
    """Return the contents of a UTF-8 text file in the workspace."""
    file_path = _resolve_workspace_path(workspace, path)
    return file_path.read_text(encoding="utf-8")


def write_file(
    workspace: str, path: str, content: str, *, run_directory: str | None = None
) -> str:
    """Create or overwrite a UTF-8 text file and return its relative path."""
    if run_directory is None:
        file_path = _resolve_workspace_path(workspace, path)
    else:
        root = _resolve_workspace_path(workspace, ".")
        relative_path = Path(path)
        if relative_path.is_absolute():
            raise ValueError("Path must be relative to the workspace root")
        if not relative_path.is_relative_to(run_directory):
            relative_path = Path(run_directory) / relative_path

        file_path = _resolve_workspace_path(workspace, str(relative_path))
        run_root = root / run_directory
        if file_path == run_root or not file_path.is_relative_to(run_root):
            raise ValueError(
                "Path must point to a file inside the current run directory"
            )
        path = str(file_path.relative_to(root))

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return path


def find_files(workspace: str, pattern: str) -> list[str]:
    """Find files by name and return paths relative to the workspace."""
    root = _resolve_workspace_path(workspace, ".")
    return sorted(
        str(path.relative_to(root))
        for path in root.rglob("*")
        if fnmatchcase(path.name, pattern) and not path.is_symlink() and path.is_file()
    )
