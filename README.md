# ThoughtMate2

CLI-ассистент для задач по программированию. Отправляет запрос в OpenRouter и выводит ответ модели в консоль. Инструменты пока не подключены.

## Локальный запуск

Понадобятся Python 3.15, `uv` и ключ OpenRouter. Из корня репозитория:

```sh
cp .env.example .env
cp src/main_agent/config/config.example.yaml src/main_agent/config/config.yaml
```

Укажи `PROVIDER_API_KEY` в `.env` и идентификатор модели OpenRouter в `llm_config.model`. Оставь `llm_config.stream: false`, поскольку агент обрабатывает ответ целиком.

```sh
uv sync
uv run python -m src.main_agent.app "Объясни, как работает async в Python"
```

[Архитектура и агентный цикл](docs/architecture.md)
