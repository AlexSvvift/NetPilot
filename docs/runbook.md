# Запуск и обслуживание

## Локальный запуск

```powershell
cd D:\PythonProjectXXX\VPN
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload
```

## Проверка после запуска

Откройте:

```text
http://127.0.0.1:8000/api/health
```

Ожидаемый ответ содержит `"status": "ok"`.

## Где лежат данные

По умолчанию SQLite хранится в `data/netpilot.db`. Файл создается автоматически
при первом запуске. Папка `data` и база исключены из Git.

## Изменение ключа

Остановите приложение, измените `API_KEY` в `.env`, затем запустите его снова.
Не вставляйте реальный ключ в README, исходный код или публичный репозиторий.

## Docker

```powershell
docker compose up --build
docker compose down
```

## Частые проблемы

### Порт 8000 занят

Запустите на другом порту:

```powershell
python -m uvicorn app.main:app --reload --port 8010
```

### PowerShell запрещает Activate.ps1

Можно не активировать окружение, а запускать Python напрямую:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

### Цель DOWN

Проверьте URL, адрес, порт, наличие сетевого доступа и значение таймаута. Для
локальных адресов вроде `192.168.x.x` компьютер должен находиться в той же
сети или иметь маршрут до этой сети.
