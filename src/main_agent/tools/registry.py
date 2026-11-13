import uuid

from src.main_agent.tools import files


def build_tools(run_directory: uuid.UUID):
    """Build the tools for one agent run."""

    def write_file(workspace: str, path: str, content: str) -> str:
        """Save a file in this run's directory."""
        return files.write_file(
            workspace, path, content, run_directory=str(run_directory)
        )

    return {
        "read_file": files.read_file,
        "write_file": write_file,
        "find_files": files.find_files,
    }
