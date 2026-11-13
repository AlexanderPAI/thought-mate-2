# ThoughtMate2

Агент для задач по программированию с HTTP API на FastAPI. Он обращается к модели через OpenRouter, ищет файлы по имени, читает и сохраняет текст в настроенных рабочих каталогах.

## Локальный запуск

Понадобятся Python 3.15, `uv` и ключ OpenRouter. При первом запуске из корня репозитория скопируй примеры конфигурации.

```sh
cp .env.example .env
cp src/main_agent/config/config.example.yaml src/main_agent/config/config.yaml
uv sync
```

Укажи `PROVIDER_API_KEY` в `.env`. В `src/main_agent/config/config.yaml` укажи идентификатор модели с поддержкой вызова инструментов в `llm_config.model` и оставь `llm_config.stream: false`. Агент обрабатывает ответ модели целиком.

```sh
uv run python -m src.main_agent.app
```

Uvicorn запускает API на порту `8080`. Документация Swagger UI доступна по адресу [localhost:8080/docs](http://localhost:8080/docs).

## HTTP API

| Метод и путь | Назначение |
| --- | --- |
| `GET /health` | Проверка доступности API. Возвращает `{"status":"ok"}`. |
| `POST /api/v1/invoke` | Запускает агента. Текст задачи передаётся в query-параметре `message`. |

```sh
curl http://127.0.0.1:8080/health

curl -X POST -G http://127.0.0.1:8080/api/v1/invoke \
  --data-urlencode 'message=Создай пример простого скрипта на Python'
```

| Поле ответа | Значение |
| --- | --- |
| `run_id` | UUID запуска. Совпадает с именем подкаталога, в который агент пишет файлы. |
| `status` | `completed` — получен финальный текст, `empty_response` — модель вернула ответ без текста и вызовов инструментов, `step_limit` — достигнут лимит шагов. |
| `provider`, `model` | Имя адаптера (`OpenRouterProvider`) и идентификатор модели из конфигурации. |
| `llm_calls` | Число обращений к модели за запуск. |
| `usage`, `cost` | Суммарные токены и стоимость по обращениям к модели. В `usage` входят `input_tokens`, `output_tokens`, `total_tokens` и `reasoning_tokens`. |
| `duration` | Длительность в секундах. При нескольких шагах текущее значение завышено. |
| `history` | Записи в порядке выполнения. Текст модели приходит строкой или `null`, результат инструмента — объектом с `role`, `tool_call_id` и `content`. При `completed` последняя запись содержит финальный текст. |

Пустой или пробельный `message` возвращает `{"status":"error","message":"No task provided. Exiting"}`.

## Конфигурация

Модуль [`config.py`](src/main_agent/config/config.py) загружает и проверяет настройки через Pydantic при старте приложения. Пути к `.env` и `config.yaml` отсчитываются от рабочего каталога процесса.

- `EnvConfig` читает обязательный ключ `PROVIDER_API_KEY` из окружения процесса или из `.env`. Переменная окружения имеет приоритет.
- `AgentConfig` читает настройки агента только из `src/main_agent/config/config.yaml`. Вложенный блок `llm_config` проверяет модель `LLMConfig`.

### Пример `config.yaml`

```yaml
llm_config:
  provider: openrouter
  base_url: https://openrouter.ai/api/v1
  model: your-model
  temperature: 0.7
  max_tokens: 1000
  stream: false

log_level: info
agent_max_steps: 10

workspaces:
  tmp: ./tmp
```

| Поле | Назначение |
| --- | --- |
| `llm_config.provider` | Провайдер модели. Допустимое значение — `openrouter`. |
| `llm_config.base_url` | Обязательное поле схемы. Сейчас клиент OpenRouter использует URL по умолчанию из SDK. |
| `llm_config.model` | Идентификатор модели OpenRouter. Для файловых операций нужна модель с поддержкой вызова инструментов. |
| `llm_config.temperature` | Параметр генерации, влияющий на вариативность ответа. |
| `llm_config.max_tokens` | Лимит токенов генерации на один запрос к модели. |
| `llm_config.stream` | Параметр потокового ответа. Для текущего агентного цикла укажи `false`. |
| `log_level` | Поле конфигурации со значением `info` по умолчанию. Текущая точка входа Uvicorn его не применяет. |
| `agent_max_steps` | Максимальное число обращений к модели за один запуск агента. |
| `workspaces` | Словарь «имя → путь» для файловых инструментов. Агент передаёт имя, например `tmp`. Относительные пути в словаре отсчитываются от корня репозитория. |

## Где искать результат

При `tmp: ./tmp` файлы одного запуска сохраняются в `tmp/<run_id>/`. Подкаталог создаётся при первой записи. `write_file` возвращает путь относительно workspace, например `<run_id>/app.py`. Его можно найти в `history` среди результатов инструментов. Поиск и чтение доступны во всём выбранном workspace, включая результаты прошлых запусков.

## Документация

- [Архитектура и агентный цикл](docs/architecture.md)

## Release notes

- [0.2.0](docs/release-notes-0.2.0.md)
- [0.1.0](docs/release-notes.md#010)
