# Geozone Service

REST API сервис геозонирования на Django + PostGIS. Позволяет создавать географические зоны, проверять попадание координат устройства в геозону и хранить историю проверок.

## Стек технологий

- Python 3.11, Django 4.2, Django REST Framework
- PostgreSQL 15 + PostGIS 3.4 (геопространственные запросы)
- Docker + Docker Compose
- drf-spectacular (Swagger / OpenAPI)
- ruff (линтер + форматирование)
- pre-commit

## Быстрый старт

```bash
docker compose up --build
```

После запуска доступны:

| URL | Описание |
|-----|----------|
| http://localhost:8000/api/docs/ | Swagger UI (интерактивная документация) |
| http://localhost:8000/api/schema/ | OpenAPI-схема (JSON) |
| http://localhost:8000/admin/ | Django Admin |
| http://localhost:8000/api/geozones/ | CRUD геозон |
| http://localhost:8000/api/geozones/check-point/ | Проверка точки |
| http://localhost:8000/api/checks/ | История проверок |

## Django Admin (создание геозоны через карту)

1. Суперпользователь создаётся автоматически при запуске:
   - **Логин:** `Admin`
   - **Пароль:** пустой (просто нажмите "Log in")
2. Откройте http://localhost:8000/admin/ и войдите
3. Перейдите в **Geozones → Add geozone**
4. Введите **Name** (например, "Склад Самара")
5. На карте OpenStreetMap используйте панель инструментов слева:
   - **Точка**  - кликните на карту, чтобы поставить точку
   - **Линия**  - кликайте точки маршрута, **двойной клик** на последней точке для завершения
   - **Полигон**  - кликайте вершины контура, **двойной клик** на последней точке для замыкания фигуры
6. Для редактирования уже нарисованной фигуры  - нажмите кнопку **Edit** (карандаш) и перетащите вершины
7. Для удаления фигуры и рисования заново  - нажмите кнопку **Delete** (корзина)
8. Нажмите **Save**

## API

### 1. Создание геозоны

```
POST /api/geozones/
Content-Type: application/json

{
  "name": "Склад Самара",
  "geometry": "POLYGON((50.1200 53.1800, 50.1800 53.1800, 50.1800 53.2200, 50.1200 53.2200, 50.1200 53.1800))"
}
```

Ответ (`201 Created`):

```json
{
  "id": 1,
  "name": "Склад Самара",
  "geometry": "SRID=4326;POLYGON ((50.12 53.18, 50.18 53.18, 50.18 53.22, 50.12 53.22, 50.12 53.18))"
}
```

Геометрия принимается в формате WKT: `POLYGON((...))`, `POINT(...)`, `MULTIPOLYGON(...)` и т.д.

### 2. Список геозон

```
GET /api/geozones/
```

### 3. Проверка точки (попадание в геозону)

```
POST /api/geozones/check-point/
Content-Type: application/json

{
  "device_id": "truck-42",
  "lat": 53.2011,
  "lon": 50.1442
}
```

Ответ (точка внутри геозоны):

```json
{
  "device_id": "truck-42",
  "lat": 53.2011,
  "lon": 50.1442,
  "inside": true,
  "matched_geozone": {
    "id": 1,
    "name": "Склад Самара"
  }
}
```

Ответ (точка вне геозон):

```json
{
  "device_id": "truck-42",
  "lat": 53.1000,
  "lon": 50.1000,
  "inside": false
}
```

Валидация: `lat` от -90 до 90, `lon` от -180 до 180. При невалидных данных возвращается `400 Bad Request`.

### 4. История проверок с фильтрацией

```
GET /api/checks/?device_id=truck-42&inside=true
```

| Параметр | Описание |
|----------|----------|
| `device_id` | Фильтр по ID устройства |
| `inside` | `true` / `false`  - только попавшие или нет |

Результаты отсортированы по дате (новые первые).

## Проверка работоспособности (PowerShell)

```powershell
# 1. Создание геозоны
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/geozones/" `
    -ContentType "application/json" `
    -Body '{"name": "Склад Самара", "geometry": "POLYGON((50.1200 53.1800, 50.1800 53.1800, 50.1800 53.2200, 50.1200 53.2200, 50.1200 53.1800))"}'

# 2. Список геозон
Invoke-RestMethod -Method Get -Uri "http://localhost:8000/api/geozones/"

# 3. Проверка точки (внутри геозоны)
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/geozones/check-point/" `
    -ContentType "application/json" `
    -Body '{"device_id": "truck-42", "lat": 53.2011, "lon": 50.1442}'

# 4. Проверка точки (вне геозоны)
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/geozones/check-point/" `
    -ContentType "application/json" `
    -Body '{"device_id": "truck-42", "lat": 53.1000, "lon": 50.1000}'

# 5. История проверок с фильтрацией
Invoke-RestMethod -Method Get -Uri "http://localhost:8000/api/checks/?device_id=truck-42&inside=true"
```

## Проверка работоспособности (curl)

```bash
# 1. Создание геозоны
curl -X POST http://localhost:8000/api/geozones/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Склад Самара", "geometry": "POLYGON((50.1200 53.1800, 50.1800 53.1800, 50.1800 53.2200, 50.1200 53.2200, 50.1200 53.1800))"}'

# 2. Список геозон
curl http://localhost:8000/api/geozones/

# 3. Проверка точки
curl -X POST http://localhost:8000/api/geozones/check-point/ \
  -H "Content-Type: application/json" \
  -d '{"device_id": "truck-42", "lat": 53.2011, "lon": 50.1442}'

# 4. История проверок
curl "http://localhost:8000/api/checks/?device_id=truck-42&inside=true"
```

## Тесты

```bash
docker compose exec web python manage.py test geozones -v2
```

## Линтер

```bash
pip install ruff
ruff check .
ruff format .
```

## Pre-commit

```bash
pip install pre-commit
pre-commit install
```

После этого ruff будет автоматически проверять код перед каждым коммитом.

## Структура проекта

```
geo/
├── docker-compose.yml          # Оркестрация контейнеров
├── Dockerfile                  # Образ приложения
├── requirements.txt            # Python-зависимости
├── pyproject.toml              # Конфигурация ruff
├── .pre-commit-config.yaml     # Хуки pre-commit
├── .gitignore
├── manage.py
├── geozone_service/            # Настройки Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── geozones/                   # Основное приложение
    ├── models.py               # Geozone, Check
    ├── views.py                # API endpoints
    ├── serializers.py          # Валидация и сериализация
    ├── urls.py                 # Маршруты API
    ├── admin.py                # Django Admin с картой
    └── tests.py                # Тесты API
```

## Логика проверки точки

Проверка выполняется на стороне PostgreSQL/PostGIS с помощью функции `ST_Contains`:

```sql
SELECT id, name FROM geozones_geozone
WHERE ST_Contains(geometry, ST_SetSRID(ST_MakePoint(lon, lat), 4326))
LIMIT 1
```

Если точка попадает в несколько геозон, возвращается первая найденная.

### Production-сценарий для множественных пересечений

В production при попадании точки в несколько геозон можно:

- Возвращать **все** совпавшие геозоны массивом, а не только первую
- Добавить поле **priority** в модель Geozone и сортировать по нему (`ORDER BY priority`)
- Использовать пространственный индекс (`CREATE INDEX ... USING GIST(geometry)`)  - Django создаёт его автоматически для `GeometryField`, что обеспечивает быстрый поиск даже при большом количестве геозон
