from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import asdict
from os import environ
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Request
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.main_agent.agent import providers
from src.main_agent.agent.agent_core import AgentCore
from src.main_agent.config.config import agent_config, env_config
from src.main_agent.infrastructure.db.sessions import (
    initialize_schema,
    load_session,
    save_history,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    engine = create_async_engine(environ["DATABASE_URL"])

    try:
        async with engine.begin() as conn:
            await conn.run_sync(initialize_schema)

        app.state.session_factory = async_sessionmaker(engine)
        yield
    finally:
        await engine.dispose()


app = FastAPI(lifespan=lifespan)
active_sessions: set[UUID] = set()

agent = AgentCore(
    provider=providers.OpenRouterProvider(
        llm_config=agent_config.llm_config,
        api_key=env_config.provider_api_key,
    )
)


@app.get("/health", status_code=200)
async def health():
    return {"status": "ok"}


@app.post("/api/v1/invoke")
async def invoke_agent(
    request: Request,
    message: str,
    session_id: UUID | None = None,
):
    if not message.strip():
        return {"status": "error", "message": "No task provided. Exiting"}

    create = session_id is None
    if session_id is None:
        session_id = uuid4()

    if session_id in active_sessions:
        raise HTTPException(409, "An agent run is already active for this session")

    active_sessions.add(session_id)
    try:
        session_factory = request.app.state.session_factory
        session = None if create else await load_session(session_factory, session_id)
        if not create and session is None:
            raise HTTPException(404, "Session not found")

        history = session.messages if session is not None else []
        workspaces = agent_config.workspaces
        if not workspaces:
            raise HTTPException(503, "No workspaces configured")
        workspace = session.workspace if session is not None else None
        if workspace is None:
            workspace = agent_config.default_workspace
            if workspace is None:
                workspace = "tmp" if "tmp" in workspaces else min(workspaces)
        if workspace not in workspaces:
            raise HTTPException(409, "The session workspace is no longer configured")

        response, new_messages = await agent.invoke(
            message, history=history, workspace=workspace
        )

        saved = await save_history(
            session_factory,
            session_id,
            history + new_messages,
            workspace=workspace,
            create=create,
        )
        if not saved:
            raise HTTPException(404, "Session not found")

        return {"session_id": session_id, "workspace": workspace, **asdict(response)}
    finally:
        active_sessions.remove(session_id)
