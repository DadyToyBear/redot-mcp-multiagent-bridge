# Godot/Redot Web + MCP мультиагентский мост

Репозиторий с инструментами для работы облачного ИИ (chat.z.ai) с веб-редактором Godot/Redot через WebFTP.

## Состав
- `multiagent-mcp.py` — MCP-сервер чата (инструменты `chat_agents`, `chat_post`, `chat_dm`, `chat_read`, `chat_assign`).
- `CHAT_PROTOCOL.md` — протокол обмена агентов через файлы на WebFTP.
- `START_HERE_FOR_CHATZAI.md` — инструкция подключения к MCP-мосту.
- `dashboard.html` — дашборд с вкладками Dashboard / Live / Чат.
- `opencode.example.json` — пример конфигурации OpenCode (секреты вынесены в env).

## Важно
- Никакие API-ключи и пароли в репозиторий не commuting — используйте `{env:OPENROUTER_API_KEY}`.
- Веб-редактор и проект размещены на OrangePi 5+, доступ по HTTPS:
  `https://91-77-164-54.sslip.io:8099/godot.editor.html`

## Orca
Оркестратор: https://github.com/stablyai/orca
