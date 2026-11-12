# ThoughtMate2

CLI-агент для задач по программированию. Он обращается к модели через OpenRouter, выполняет вызовы файловых инструментов и выводит ответ в консоль. Агент умеет искать файлы по имени, читать и сохранять текстовые файлы в настроенных рабочих каталогах.

## Локальный запуск

Понадобятся Python 3.15, `uv` и ключ OpenRouter. При первом запуске из корня репозитория скопируй примеры конфигурации.

```sh
cp .env.example .env
cp src/main_agent/config/config.example.yaml src/main_agent/config/config.yaml
uv sync
```

Укажи `PROVIDER_API_KEY` в `.env`. В `src/main_agent/config/config.yaml` укажи идентификатор модели с поддержкой вызова инструментов в `llm_config.model` и оставь `llm_config.stream: false`. Агент обрабатывает ответ модели целиком.

```sh
uv run python -m src.main_agent.app "Создай скрипт на Python с простым FastAPI-приложением"
```

## Конфигурация

Модуль [`config.py`](src/main_agent/config/config.py) загружает и проверяет настройки через Pydantic при старте приложения. Пути к `.env` и `config.yaml` отсчитываются от каталога запуска CLI.

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
| `log_level` | Уровень логирования агента. Допустимы `debug`, `info`, `warning`, `error`. Значение по умолчанию — `info`. |
| `agent_max_steps` | Максимальное число обращений к модели за один запуск агента. |
| `workspaces` | Словарь «имя → путь» для файловых инструментов. Агент передаёт имя, например `tmp`. Относительные пути в словаре отсчитываются от корня репозитория. |

На уровне `info` видны шаги, вызовы инструментов и текст ответа. На уровне `debug` также видны рассуждения модели или их сводка, если провайдер вернул эти данные.

## Где искать результат

При `tmp: ./tmp` каждый запрос получает отдельный подкаталог `tmp/run-<id>/`, который создаётся при первой записи. Все файлы, сохранённые за один запуск, попадают в этот подкаталог. Строка `Saved file in workspace tmp: run-<id>/app.py` показывает, где найти результат. Поиск и чтение доступны во всём выбранном workspace, включая результаты прошлых запусков.

## Документация

- [Архитектура и агентный цикл](docs/architecture.md)

## Release notes

- [0.1.0](docs/release-notes.md#010)
