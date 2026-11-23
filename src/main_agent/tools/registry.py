import uuid

from src.main_agent.tools import files
from src.main_agent.tools.knowledge import search_knowledge


def build_tools(run_directory: uuid.UUID, workspace: str):
    """Build the tools for one agent run."""

    def read_file(path: str) -> str:
        return files.read_file(workspace, path)

    def write_file(path: str, content: str) -> str:
        return files.write_file(
            workspace,
            path,
            content,
            run_directory=str(run_directory),
        )

    def find_files(pattern: str) -> list[str]:
        return files.find_files(workspace, pattern)

    return {
        "read_file": read_file,
        "write_file": write_file,
        "find_files": find_files,
        "search_knowledge": search_knowledge,
    }
