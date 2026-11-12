from fastapi import FastAPI

from src.main_agent.agent.agent_core import AgentCore

app = FastAPI()

agent = AgentCore()


@app.get("/health", status_code=200)
async def health():
    return {"status": "ok"}


@app.post("/api/v1/invoke")
async def invoke_agent(message: str):
    if not message.strip():
        return {"status": "error", "message": "No task provided. Exiting"}
    result = await agent.invoke(message)
    return {"status": "ok", "agent_result": result}
