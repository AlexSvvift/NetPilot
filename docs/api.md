# API NetPilot

Базовый адрес локального сервиса:

```text
http://127.0.0.1:8000/api
```

Интерактивная документация: `http://127.0.0.1:8000/docs`.

## Открытые endpoints

### GET `/health`

Проверяет, что приложение запущено.

Ответ:

```json
{
  "status": "ok",
  "service": "NetPilot",
  "monitoring_enabled": true
}
```

### GET `/dashboard`

Возвращает общие числа и список целей с последним результатом проверки.

### GET `/targets`

Возвращает все цели.

## Изменяющие endpoints

Если в `.env` задан `API_KEY`, передавайте его заголовком:

```text
X-API-Key: change-me
```

### POST `/targets`

HTTP-цель:

```json
{
  "name": "Main website",
  "kind": "http",
  "url": "https://example.com",
  "interval_seconds": 60,
  "timeout_seconds": 5
}
```

TCP-цель:

```json
{
  "name": "VPN server",
  "kind": "tcp",
  "host": "203.0.113.10",
  "port": 443,
  "interval_seconds": 30,
  "timeout_seconds": 3
}
```

UDP-цель имеет такую же форму, но `kind` равен `udp`.

### PATCH `/targets/{id}`

Можно изменить отдельные поля:

```json
{
  "enabled": false,
  "interval_seconds": 120
}
```

### DELETE `/targets/{id}`

Удаляет цель вместе с ее историей проверок. Ответ - `204 No Content`.

### POST `/targets/{id}/check`

Запускает одну проверку сразу и сохраняет результат.

### GET `/targets/{id}/history?limit=50`

Возвращает последние результаты конкретной цели.

## Основные коды ответа

| Код | Значение |
| --- | --- |
| `200` | запрос выполнен |
| `201` | объект создан |
| `204` | объект удален, тело ответа пустое |
| `401` | неверный или отсутствующий API-ключ |
| `404` | цель не найдена |
| `422` | данные не прошли валидацию |
| `500` | внутренняя ошибка сервера |

