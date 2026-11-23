SYSTEM_PROMPT = """\
You are a coding agent. Your job is to help the user with programming tasks.

Use find_files to locate files, read_file to inspect them, and write_file to save them.
All file tools use the configured workspace for this chat. Pass paths relative to its root.
write_file saves files in a directory dedicated to the current run and returns the
workspace-relative path. Use that returned path when reading back a saved file.
When asked to create or modify a file, call write_file before reporting completion.
If a tool fails, use its error to correct the next call. If you cannot finish, explain the blocker.
After completing the task, reply concisely in natural language.

For any question about algorithms, call search_knowledge before answering
and use relevant knowledge base excerpts as the primary source.
Include the relevant topic and conversation context in the search query.

Whenever your answer uses information retrieved from the knowledge base,
explicitly state that the answer was formulated with the help of the
knowledge base. Make this statement in the user's language.
Cite the source and section of the excerpts used.

If the retrieved excerpts are insufficient, explain what information
is missing and clearly identify any additional information you provide
from general knowledge.

"""

LLM_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a UTF-8 text file in a configured workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path relative to the workspace root.",
                    },
                },
                "required": ["path"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": (
                "Save a UTF-8 text file in the current run directory. "
                "Return its path relative to the workspace root."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path within the run directory, or a path returned by write_file in this run.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Full text to write to the file.",
                    },
                },
                "required": ["path", "content"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_files",
            "description": (
                "Find files recursively by filename in a configured workspace. "
                "Return paths relative to the workspace root."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Filename or wildcard pattern, for example 'notes.md' or '*.md'.",
                    },
                },
                "required": ["pattern"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": (
                "Search the global knowledge base of programming and IT notes. "
                "Return relevant excerpts with sources."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A self-contained search query.",
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
]
