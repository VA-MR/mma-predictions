# Запуск Админ-панели MMA Project

## Быстрый старт

### 1. Запуск Backend (API)

```bash
cd "/Users/v/Desktop/MMA project"

# Остановить все запущенные серверы
lsof -ti:8000 | xargs kill -9 2>/dev/null

# Запустить backend
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend будет доступен на `http://localhost:8000`

### 2. Запуск Frontend

Откройте новый терминал:

```bash
cd "/Users/v/Desktop/MMA project/frontend"

# Установить зависимости (если еще не установлены)
npm install

# Запустить dev сервер
npm run dev
```

Frontend будет доступен на `http://localhost:5173`

### 3. Открыть админ-панель

Откройте браузер и перейдите по адресу:
- **Frontend:** http://localhost:5173/admin
- **API Docs:** http://localhost:8000/docs

## Проверка работоспособности

### Проверка Backend API

```bash
# Проверка здоровья API
curl http://localhost:8000/health

# Проверка данных
curl http://localhost:8000/api/admin/fighters?limit=3
curl http://localhost:8000/api/admin/events?limit=3
curl http://localhost:8000/api/admin/fights?limit=3
curl http://localhost:8000/api/admin/organizations
```

### Проверка данных в БД

```bash
cd "/Users/v/Desktop/MMA project"
python3 -c "
from database.db import Database
from database.models import Fighter, Event, Fight
from sqlalchemy import func

db = Database('mma_data.db')
session = db.get_session()

print('=== DATABASE STATS ===')
print(f'Fighters: {session.query(func.count(Fighter.id)).scalar()}')
print(f'Events: {session.query(func.count(Event.id)).scalar()}')
print(f'Fights: {session.query(func.count(Fight.id)).scalar()}')
print(f'Organizations: {session.query(func.count(func.distinct(Event.organization))).scalar()}')
"
```

### Тестовый скрипт

```bash
cd "/Users/v/Desktop/MMA project"
python3 test_admin_api.py
```

## Структура данных

### Данные из парсера

Все данные находятся в БД `mma_data.db`:

- **1,081 бойцов** (fighters)
- **55 событий** (events)
- **518 боев** (fights)
- **12 организаций** (извлекаются из events)

### API Endpoints

**Organizations:**
- `GET /api/admin/organizations` - Список всех организаций

**Fighters:**
- `GET /api/admin/fighters` - Список бойцов (с поиском)
- `GET /api/admin/fighters/{id}` - Получить бойца
- `POST /api/admin/fighters` - Создать бойца
- `PUT /api/admin/fighters/{id}` - Обновить бойца
- `DELETE /api/admin/fighters/{id}` - Удалить бойца

**Events:**
- `GET /api/admin/events` - Список событий
- `GET /api/admin/events/{id}` - Получить событие
- `POST /api/admin/events` - Создать событие
- `PUT /api/admin/events/{id}` - Обновить событие
- `DELETE /api/admin/events/{id}` - Удалить событие

**Fights:**
- `GET /api/admin/fights` - Список боев
- `GET /api/admin/fights/{id}` - Получить бой
- `POST /api/admin/fights` - Создать бой
- `PUT /api/admin/fights/{id}` - Обновить бой
- `DELETE /api/admin/fights/{id}` - Удалить бой

## Решение проблем

### Backend не запускается

```bash
# Проверить, занят ли порт 8000
lsof -i:8000

# Убить процесс на порту 8000
lsof -ti:8000 | xargs kill -9

# Запустить заново
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend не подключается к API

1. Убедитесь, что backend запущен на порту 8000
2. Проверьте консоль браузера на ошибки CORS
3. Проверьте, что frontend запущен на порту 5173

### Данные не отображаются

1. Проверьте, что БД содержит данные (см. "Проверка данных в БД")
2. Проверьте API через curl (см. "Проверка Backend API")
3. Откройте консоль браузера (F12) и проверьте Network tab
4. Запустите тестовый скрипт: `python3 test_admin_api.py`

### Обновление данных из парсера

Чтобы обновить данные из парсера:

```bash
cd "/Users/v/Desktop/MMA project"

# Запустить парсер для всех событий
python3 main.py

# Или для конкретного события
python3 main.py --event aca-197

# Показать статистику БД
python3 main.py --stats
```

## Полезные команды

```bash
# Просмотр логов backend
tail -f /Users/v/.cursor/projects/Users-v-Desktop-MMA-project/terminals/*.txt

# Проверка всех endpoints
curl http://localhost:8000/openapi.json | python3 -m json.tool | grep -A 5 "admin"

# Остановить все процессы
pkill -f uvicorn
pkill -f "npm run dev"
```

## Архитектура

```
┌─────────────────┐
│   Frontend      │  http://localhost:5173
│   (React+Vite)  │
└────────┬────────┘
         │ API calls
         ↓
┌─────────────────┐
│   Backend API   │  http://localhost:8000
│   (FastAPI)     │
└────────┬────────┘
         │ SQLAlchemy
         ↓
┌─────────────────┐
│   mma_data.db   │  SQLite Database
│   (Парсер)      │
└─────────────────┘
```

## Дополнительная информация

- **API документация:** http://localhost:8000/docs
- **OpenAPI схема:** http://localhost:8000/openapi.json
- **Подробная документация:** См. `ADMIN_README.md`

