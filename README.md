# ThoughtMate2

Агент для задач по программированию с веб-чатом и HTTP API на FastAPI. Он обращается к модели через OpenRouter, хранит контекст диалогов в PostgreSQL, работает с файлами и ищет по глобальной базе знаний в Qdrant.

## Что умеет агент

- **Вести диалог о коде.** Отвечает на вопросы в веб-чате с поддержкой Markdown и через HTTP API. Продолжает разговор с сохранённым контекстом сессии.
- **Работать с файлами.** Ищет файлы по имени и читает текст в настроенном рабочем каталоге. Результаты записывает в отдельную папку текущего запуска.
- **Искать по конспектам.** Находит релевантные фрагменты из проиндексированных Markdown-документов по смыслу запроса и указывает использованные источники и разделы в ответе.
- **Выполнять задачи в несколько шагов.** Например, находит файл, читает его и сохраняет результат в новом файле. API возвращает статус запуска, результаты вызовов инструментов и расход токенов.

## Дорожная карта

- [План развития](docs/plan/plan.md) — этапы и критерии готовности.
- [Чек-лист](docs/plan/checklist.md) — задачи и проверки для отслеживания прогресса.
- [План релизов](docs/plan/releases.md) — фичи по версиям, спринты и условия выпуска.

### Планируемые релизы

| Версия | Что планируется |
|---|---|
| `0.5.0` | Независимый выбор Ollama или OpenRouter для чата и эмбеддингов. Полностью локальный профиль работает без ключа OpenRouter. |
| `0.6.0` | Режим «База знаний» с ответами по конспектам и ссылками на источники. |
| `0.7.0` | Поиск и объяснение кода в настроенном рабочем каталоге со ссылками на файлы и строки. |
| `0.8.0` | Предложение небольших правок в виде diff с проверкой применимости. |
| `0.9.0` | Локальный агент через Ollama с поиском, чтением и записью файлов в рамках заданных лимитов. |

## Локальный запуск

Понадобится ключ OpenRouter. При первом запуске из корня репозитория скопируй примеры конфигурации.

```sh
cp .env.example .env
cp src/main_agent/config/config.example.yaml src/main_agent/config/config.yaml
```

Укажи `PROVIDER_API_KEY` в `.env`. В `src/main_agent/config/config.yaml` укажи идентификатор модели с поддержкой вызова инструментов в `llm_config.model` и оставь `llm_config.stream: false`. Агент обрабатывает ответ модели целиком. Блок `knowledge` заполни по [примеру ниже](#пример-configyaml). В текущем `config.example.yaml` поля `embedding_model` и `top_k` находятся в `llm_config`; перенеси их в `knowledge` и укажи `sources: [./knowledge]`.

### Docker Compose

После настройки `.env` и `config.yaml` запусти чат, API, PostgreSQL и Qdrant через Docker Compose.

```sh
mkdir -p tmp knowledge
docker compose up -d --build app chat-ui postgres qdrant
```

Открой [веб-чат](http://localhost:3000) или [Swagger UI](http://localhost:8080/docs). Чат отображает Markdown в ответах агента. Кнопка «Новый чат» и перезагрузка страницы начинают новый диалог. Рабочий каталог задаётся в `config.yaml`. После изменения конфига пересобери `app`, поскольку конфиг копируется в образ. Перед первым поиском выполни [индексацию базы знаний](#индексация-базы-знаний).

### API без Docker

Понадобятся Python 3.15, `uv` и доступная база PostgreSQL. Укажи её адрес в переменной окружения `DATABASE_URL`. FastAPI создаст таблицу сессий при запуске.

```sh
uv sync
DATABASE_URL='postgresql+asyncpg://user:password@localhost:5432/thoughtmate' \
  uv run python -m src.main_agent.app
```

Схема HTTP API доступна в [Swagger UI](http://localhost:8080/docs). Для поиска и индексации при локальном запуске укажи `knowledge.qdrant_url: http://127.0.0.1:6333`. Qdrant можно запустить командой `docker compose up -d qdrant`.

## HTTP API

После запуска приложения доступны [Swagger UI](http://localhost:8080/docs) и [схема FastAPI в JSON](http://localhost:8080/openapi.json). YAML ниже дополнительно описывает поля фактических ответов и ошибки обработчика.

<details>
<summary>Контракт OpenAPI 3.1 (YAML)</summary>

```yaml
openapi: 3.1.0
info:
  title: ThoughtMate2 HTTP API
  version: 0.4.0
servers:
  - url: http://localhost:8080
paths:
  /health:
    get:
      summary: Проверить доступность API
      responses:
        '200':
          description: API отвечает
          content:
            application/json:
              schema:
                type: object
                required: [status]
                properties:
                  status: { type: string, const: ok }
  /api/v1/invoke:
    post:
      summary: Запустить агента
      parameters:
        - name: message
          in: query
          required: true
          schema: { type: string }
        - name: session_id
          in: query
          description: UUID существующей сессии. Если параметр опущен, создаётся новая сессия.
          schema: { type: string, format: uuid }
      responses:
        '200':
          description: Результат запуска или сообщение о пустом запросе
          content:
            application/json:
              schema:
                oneOf:
                  - $ref: '#/components/schemas/AgentRun'
                  - $ref: '#/components/schemas/EmptyMessage'
        '404':
          description: Сессия не найдена
          content:
            application/json:
              schema: { $ref: '#/components/schemas/HTTPError' }
        '409':
          description: Для сессии уже выполняется запрос или её рабочий каталог удалён из конфигурации
          content:
            application/json:
              schema: { $ref: '#/components/schemas/HTTPError' }
        '422':
          description: Параметр message отсутствует или session_id имеет неверный формат
          content:
            application/json:
              schema: { $ref: '#/components/schemas/ValidationError' }
        '503':
          description: Рабочие каталоги не настроены
          content:
            application/json:
              schema: { $ref: '#/components/schemas/HTTPError' }
components:
  schemas:
    AgentRun:
      type: object
      required: [session_id, workspace, run_id, status, provider, model, llm_calls, duration, usage, cost, history]
      properties:
        session_id: { type: string, format: uuid }
        workspace: { type: string }
        run_id:
          type: string
          format: uuid
          description: Идентификатор запуска и имя подкаталога для записи файлов.
        status:
          type: string
          enum: [completed, empty_response, step_limit]
          description: Финальный ответ получен, модель вернула пустой ответ или достигнут лимит шагов.
        provider: { type: string, examples: [OpenRouterProvider] }
        model: { type: string }
        llm_calls: { type: integer }
        duration:
          type: number
          description: Длительность в секундах. При нескольких шагах текущее значение завышено.
        usage:
          $ref: '#/components/schemas/TokenUsage'
          description: Токены чат-модели за запуск. Эмбеддинги базы знаний сюда не входят.
        cost:
          type: number
          description: Суммарная стоимость обращений к чат-модели.
        history:
          type: array
          description: Текст модели и результаты инструментов в порядке выполнения. При completed последняя запись содержит финальный текст.
          items:
            oneOf:
              - type: [string, 'null']
              - $ref: '#/components/schemas/ToolResult'
    TokenUsage:
      type: object
      required: [input_tokens, output_tokens, total_tokens, reasoning_tokens]
      properties:
        input_tokens: { type: integer }
        output_tokens: { type: integer }
        total_tokens: { type: integer }
        reasoning_tokens: { type: integer }
    ToolResult:
      type: object
      required: [role, tool_call_id, content]
      properties:
        role: { type: string, const: tool }
        tool_call_id: { type: string }
        content: { type: string }
    EmptyMessage:
      type: object
      required: [status, message]
      properties:
        status: { type: string, const: error }
        message: { type: string, const: No task provided. Exiting }
    HTTPError:
      type: object
      required: [detail]
      properties:
        detail: { type: string }
    ValidationError:
      type: object
      required: [detail]
      properties:
        detail:
          type: array
          items:
            type: object
            required: [loc, msg, type]
            properties:
              loc:
                type: array
                items: { type: [string, integer] }
              msg: { type: string }
              type: { type: string }
              input: {}
              ctx: { type: object }
```

</details>

### Примеры запросов

```sh
curl http://127.0.0.1:8080/health

curl -X POST -G http://127.0.0.1:8080/api/v1/invoke \
  --data-urlencode 'message=Создай пример простого скрипта на Python'

# Подставь session_id из ответа на первый запрос.
curl -X POST -G http://127.0.0.1:8080/api/v1/invoke \
  --data-urlencode 'message=Объясни, что делает этот скрипт' \
  --data-urlencode 'session_id=<UUID>'
```

## Конфигурация

Модуль [`config.py`](src/main_agent/config/config.py) загружает и проверяет настройки через Pydantic при старте приложения. Пути к `.env` и `config.yaml` отсчитываются от рабочего каталога процесса.

- `EnvConfig` читает обязательный ключ `PROVIDER_API_KEY` из окружения процесса или из `.env`. Переменная окружения имеет приоритет.
- `AgentConfig` читает настройки агента только из `src/main_agent/config/config.yaml`. Вложенные блоки `llm_config` и `knowledge` проверяют модели `LLMConfig` и `KnowledgeConfig`.

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
default_workspace: tmp

knowledge:
  qdrant_url: http://qdrant:6333
  collection_alias: knowledge
  sources:
    - ./knowledge
  embedding_model: qwen/qwen3-embedding-8b
  top_k: 5
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
| `workspaces` | Словарь «имя → путь» для файловых инструментов. Относительные пути отсчитываются от корня репозитория. |
| `default_workspace` | Имя из `workspaces` для новых диалогов. Если поле опущено, используется `tmp`, если он настроен, иначе первое имя по алфавиту. Существующий диалог сохраняет привязку к своему каталогу. |
| `knowledge.qdrant_url` | Адрес Qdrant. В сети Compose — `http://qdrant:6333`, с хоста — `http://127.0.0.1:6333`. |
| `knowledge.collection_alias` | Постоянное имя опубликованной базы, используемое при поиске. |
| `knowledge.sources` | Каталоги с Markdown-конспектами. Относительные пути отсчитываются от рабочего каталога процесса. |
| `knowledge.embedding_model` | Модель OpenRouter для эмбеддингов документов и поисковых запросов. |
| `knowledge.top_k` | Максимальное число фрагментов в поисковой выдаче. |

## База знаний

База знаний общая для всех диалогов. Конспекты хранятся в `knowledge/`, например `knowledge/algoritms/6. Бинарный поиск.md`. Индексатор рекурсивно читает непустые файлы `*.md` в UTF-8. Название берётся из имени файла, источник — из пути относительно настроенного каталога.

Markdown разбирается на разделы по заголовкам. Длинные разделы делятся между абзацами и другими блоками с ориентиром 4000 символов. Отдельные таблицы, списки и блоки кода сохраняются целиком и могут превышать этот размер. Каждый фрагмент содержит название документа, путь раздела и номер внутри документа.

Compose монтирует `./knowledge` в `/app/knowledge` для чтения. При рабочем каталоге `/app` настройка `sources: [./knowledge]` подходит для контейнера и локального запуска из корня репозитория. Данные Qdrant хранятся в именованном томе `qdrant_data`.

### Индексация базы знаний

После запуска сервисов сначала проверь нарезку. Команда выводит каждый фрагмент целиком и итоговое количество документов и фрагментов.

```sh
docker compose exec app /app/.venv/bin/python \
  -m src.main_agent.knowledge.index --dry-run
```

Для получения эмбеддингов, записи в Qdrant и публикации коллекции выполни команду без `--dry-run`.

```sh
docker compose exec app /app/.venv/bin/python \
  -m src.main_agent.knowledge.index
```

Индексатор добавляет заголовки к тексту каждого фрагмента, получает эмбеддинги через OpenRouter пакетами по 16 текстов, загружает точки с текстами и метаданными в Qdrant и проверяет число записей. После загрузки переключает алиас из `knowledge.collection_alias` на итоговую коллекцию. Успешное завершение отмечается строкой `Опубликована база знаний: knowledge → knowledge_<UUID>`.

Повторяй команду после добавления, изменения или удаления конспектов. Каждый запуск заново вычисляет эмбеддинги всех фрагментов и публикует новую версию базы. Исходники доступны через том, поэтому после редактирования конспектов достаточно запустить индексацию. После изменения Python-кода или конфигурации сначала выполни `docker compose up -d --build app`.

Для локального запуска из корня репозитория используй адрес Qdrant `http://127.0.0.1:6333` в конфигурации.

```sh
uv run python -m src.main_agent.knowledge.index --dry-run
uv run python -m src.main_agent.knowledge.index
```

Оба режима загружают настройки приложения, включая `PROVIDER_API_KEY`. Полная индексация отправляет тексты в OpenRouter и расходует средства на эмбеддинги. При смене embedding-модели пересобери индекс и согласованно обнови модель поисковых запросов.

### Проверка поиска

После публикации выполни запрос через CLI.

```sh
docker compose exec app /app/.venv/bin/python \
  -m src.main_agent.knowledge.search \
  'Почему поиск в отсортированном массиве быстрее?'
```

Локальный вариант:

```sh
uv run python -m src.main_agent.knowledge.search \
  'Почему поиск в отсортированном массиве быстрее?'
```

Команда показывает число фрагментов в опубликованной коллекции и до `top_k` результатов с оценкой сходства, источником, разделом и текстом. Каждый поисковый запрос получает собственный эмбеддинг через OpenRouter. Оценка сходства помогает ранжировать результаты; для проверки качества прочитай найденные фрагменты и проверь, содержат ли они ответ.

### Поиск в чате

Инструмент `search_knowledge(query)` зарегистрирован в общем реестре. По системному промпту агент сначала обращается к базе для любого вопроса об алгоритмах. При использовании найденных материалов он должен явно сообщить, что ответ сформулирован с помощью базы знаний, и указать источники и разделы. Если материалов недостаточно, промпт требует объяснить пробелы и обозначить дополнения из общих знаний модели.

`tools/knowledge.py` создаёт и закрывает клиентов на время вызова и преобразует ошибки поиска в сообщение инструмента. `knowledge/search.py` выполняет поиск. `AgentCore` ожидает результат асинхронного инструмента и передаёт его модели через сообщение `tool`.

### Текущие ограничения

- В `write_collection()` создание коллекции и загрузка находятся внутри цикла по фрагментам. При N фрагментах создаются N коллекций с нарастающим набором точек. Публикуется последняя, содержащая все фрагменты; промежуточные коллекции увеличивают время записи и расход диска.
- Предыдущие и промежуточные коллекции автоматически не удаляются. При сбое до публикации алиас продолжает указывать на предыдущую версию.
- Подсчёт размера чанков выполняется в символах. Отдельной проверки токенного лимита embedding-модели нет.
- Поиск возвращает ближайшие фрагменты без порога сходства. Даже посторонний вопрос может получить выдачу.
- Источники из разных каталогов получают относительные пути. Следи, чтобы эти пути позволяли однозначно определить конспект.

## Где искать результат

При `tmp: ./tmp` файлы одного запуска сохраняются в `tmp/<run_id>/` в корне репозитория. Docker Compose монтирует этот каталог в `/app/tmp`. Подкаталог запуска создаётся при первой записи. `write_file` возвращает путь относительно workspace, например `<run_id>/app.py`. Его можно найти в `history` среди результатов инструментов. Поиск и чтение доступны во всём выбранном workspace, включая результаты прошлых запусков.

## Документация

- [Архитектура и агентный цикл](docs/architecture.md)

## Release notes

- [0.4.0](docs/release-notes-0.4.0.md)
- [0.3.0](docs/release-notes-0.3.0.md)
- [0.2.0](docs/release-notes-0.2.0.md)
- [0.1.0](docs/release-notes-0.1.0.md#010)
