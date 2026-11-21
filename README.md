# Redot Web + MCP Bridge + Multiagent Chat

Репозиторий содержит **шаблоны и инструменты** для сборки собственного моста между
облачным ИИ и веб-редактором Godot/Redot через WebFTP.

> ⚠️ **Важно.** В репозитории намеренно нет рабочих IP-адресов, доменов, токенов шары
> и API-ключей. Используйте только свои серверы, домены и ключи. Не используйте
> чужую инфраструктуру без разрешения — это незаконно.

## Что внутри

| Файл / папка | Назначение |
|---|---|
| `template/` | **Стартовый шаблон**: пустой MCP Dashboard, который нужно заполнить своими данными |
| `multiagent-mcp.py` | MCP-сервер чата (`chat_agents`, `chat_post`, `chat_dm`, `chat_read`, `chat_assign`) |
| `agent-host.py` | Хост агентов: читает DM с шары, вызывает модели, публикует ответы |
| `bridge.py`, `mcp_call.py` | Примеры моста «WebFTP ↔ Godot MCP Pro» (скопированы с шары) |
| `dashboard.html`, `godot.editor.html` | Примеры дашборда и редактора (только для изучения) |
| `CHAT_PROTOCOL.md`, `RULES_FOR_AGENTS.md` | Протокол обмена и правила агентов |
| `docs/` | Сборка, настройка OrangePi, диагностика |

## Быстрый старт (своя инфраструктура)

1. Скопируйте `template/` в отдельный каталог.
2. Откройте `template/config.example.json` и замените все плейсхолдеры:
   - `<YOUR_WEBFTP_SHARE_URL>` — URL вашей WebFTP-шары;
   - `<YOUR_HTTPS_ORIGIN>` — ваш HTTPS-источник (нужен для SharedArrayBuffer);
   - `<YOUR_LLM_API_KEY>` — ваш ключ, задайте переменную окружения;
   - `<YOUR_PROXY_URL>` — при необходимости.
3. Заполните `template/dashboard.template.html` — это тестовый MCP Dashboard,
   где все адреса и методы нужно прописать самостоятельно.
4. Запустите свой bridge и редактор по инструкции из `docs/BUILD.md`.

## Sekrety

- Никогда не коммитьте API-ключи и пароли. Используйте переменные окружения:
  - `WEBFTP_SHARE`
  - `OPENROUTER_API_KEY`
  - `OR_PROXY`
- Пример: `"apiKey": "{env:OPENROUTER_API_KEY}"` в `opencode.example.json`.

Подробности: [docs/BUILD.md](docs/BUILD.md).
