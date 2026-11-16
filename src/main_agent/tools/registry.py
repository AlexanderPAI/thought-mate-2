import uuid

from src.main_agent.tools import files


def build_tools(run_directory: uuid.UUID, workspace: str):
    """Build the tools for one agent run."""

    def read_file(path: str) -> str:
        return files.read_file(workspace, path)

    def write_file(path: str, content: str) -> str:
        """Save a file in this run's directory."""
        return files.write_file(
            workspace, path, content, run_directory=str(run_directory)
        )

    def find_files(pattern: str) -> list[str]:
        return files.find_files(workspace, pattern)

    return {
        "read_file": read_file,
        "write_file": write_file,
        "find_files": find_files,
    }
