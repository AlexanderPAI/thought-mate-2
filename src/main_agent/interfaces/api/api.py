from fastapi import FastAPI

from src.main_agent.agent import providers
from src.main_agent.agent.agent_core import AgentCore
from src.main_agent.config.config import agent_config, env_config

app = FastAPI()

agent = AgentCore(
    provider=providers.OpenRouterProvider(
        llm_config=agent_config.llm_config, api_key=env_config.provider_api_key
    )
)


@app.get("/health", status_code=200)
async def health():
    return {"status": "ok"}


@app.post("/api/v1/invoke")
async def invoke_agent(message: str):
    if not message.strip():
        return {"status": "error", "message": "No task provided. Exiting"}
    result = await agent.invoke(message)
    return result
