SYSTEM_PROMPT = """\
You are a coding agent. Your job is to help the user with programming tasks.

Use find_files to locate files, read_file to inspect them, and write_file to save them.
Use a configured workspace name and paths relative to that workspace.
write_file saves files in a directory dedicated to the current run and returns the
workspace-relative path. Use that returned path when reading back a saved file.
When asked to create or modify a file, call write_file before reporting completion.
If a tool fails, use its error to correct the next call. If you cannot finish, explain the blocker.
After completing the task, reply concisely in natural language.

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
                    "workspace": {
                        "type": "string",
                        "description": "Configured workspace name, for example 'tmp'.",
                    },
                    "path": {
                        "type": "string",
                        "description": "File path relative to the workspace root.",
                    },
                },
                "required": ["workspace", "path"],
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
                    "workspace": {
                        "type": "string",
                        "description": "Configured workspace name, for example 'tmp'.",
                    },
                    "path": {
                        "type": "string",
                        "description": "Path within the run directory, or a path returned by write_file in this run.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Full text to write to the file.",
                    },
                },
                "required": ["workspace", "path", "content"],
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
                    "workspace": {
                        "type": "string",
                        "description": "Configured workspace name, for example 'tmp'.",
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Filename or wildcard pattern, for example 'notes.md' or '*.md'.",
                    },
                },
                "required": ["workspace", "pattern"],
                "additionalProperties": False,
            },
        },
    },
]
