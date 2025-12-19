# خلاصه تغییرات پروژه Telegram Crawler

## تغییرات اصلی

### ✅ مرحله 1: حذف Webhook به Laravel
- پیام‌ها و رویدادها دیگر به Laravel ارسال نمی‌شوند
- همه داده‌ها در MongoDB ذخیره می‌شوند

### ✅ مرحله 2: حذف SQLite و استفاده کامل از MongoDB
- SQLAlchemy، Alembic و aiosqlite حذف شدند
- اطلاعات session ها اکنون در MongoDB ذخیره می‌شوند
- تمام عملیات به async تبدیل شدند

## فایل‌های تغییر یافته

### حذف شده
- ❌ `app/models/session.py` - مدل SQLAlchemy
- ❌ `app/models/__init__.py`
- ❌ `alembic.ini` - تنظیمات migration
- ❌ وابستگی‌های SQLAlchemy از `requirements.txt`
- ❌ `DATABASE_URL` از تمام فایل‌های config

### افزوده شده
- ✅ `app/services/mongodb.py` - سرویس جامع MongoDB
- ✅ `MONGODB_MIGRATION.md` - راهنمای migration

### بازنویسی شده
- 🔄 `app/utils/session_manager.py` - MongoDB async بجای SQLAlchemy
- 🔄 `app/api/routes.py` - تبدیل تمام فراخوانی‌ها به async
- 🔄 `app/main.py` - اضافه شدن MongoDB initialization
- 🔄 `requirements.txt` - حذف SQL، اضافه Motor/PyMongo
- 🔄 `app/config.py` - حذف database_url
- 🔄 `.env.example` - حذف DATABASE_URL
- 🔄 `.env.production` - حذف DATABASE_URL
- 🔄 `docker-compose.yml` - حذف SQLite volumes

## ساختار MongoDB

### Collections
1. **telegram_sessions** - اطلاعات اتصالات تلگرام
2. **messages** - پیام‌های دریافتی و ارسالی
3. **events** - رویدادهای تلگرام

### Indexes
```javascript
// telegram_sessions
db.telegram_sessions.createIndex({ session_id: 1 }, { unique: true })
db.telegram_sessions.createIndex({ agent_id: 1 })
db.telegram_sessions.createIndex({ phone: 1 })

// messages
db.messages.createIndex({ session_id: 1, created_at: -1 })
db.messages.createIndex({ agent_id: 1, created_at: -1 })
db.messages.createIndex({ chat_id: 1, date: -1 })

// events
db.events.createIndex({ session_id: 1, created_at: -1 })
db.events.createIndex({ agent_id: 1, event_type: 1 })
```

## تغییرات کد

### Session Manager
```python
# قبل (Sync + SQLAlchemy)
session = session_manager.get_session_by_id(session_id)
phone = session.phone

# بعد (Async + MongoDB)
session = await session_manager.get_session_by_id(session_id)
phone = session.get("phone")
```

### تمام متدهای SessionManager
- `create_session()` → `async create_session()`
- `get_session_by_id()` → `async get_session_by_id()`
- `get_session_by_phone()` → `async get_session_by_phone()`
- `get_sessions_by_agent()` → `async get_sessions_by_agent()`
- `get_all_active_sessions()` → `async get_all_active_sessions()`
- `update_session_phone()` → `async update_session_phone()`
- `update_session_connected()` → `async update_session_connected()`
- `update_session_activity()` → `async update_session_activity()`
- `update_session_metadata()` → `async update_session_metadata()`
- `deactivate_session()` → `async deactivate_session()`
- `delete_session()` → `async delete_session()`
- `cleanup_old_sessions()` → `async cleanup_old_sessions()`

## Stack فعلی

### Backend
- **FastAPI** - REST API Framework
- **Telethon** - Telegram MTProto Client
- **Motor + PyMongo** - MongoDB Async Driver
- **Redis** - Caching & Queueing

### Database
- **MongoDB** - Primary Database (تمام داده‌ها)
- **Redis** - Cache & Session Store

### Deployment
- **Docker + Docker Compose**
- **Python 3.11+**

## دستورات اجرا

```bash
# نصب dependencies
pip install -r requirements.txt

# اجرا با Docker
docker-compose up -d

# مشاهده logs
docker-compose logs -f app

# دسترسی به MongoDB
docker exec -it telegram-mongodb mongosh -u admin -p password

# متوقف کردن
docker-compose down

# پاک کردن volume ها
docker-compose down -v
```

## Health Check

```bash
# بررسی وضعیت API
curl http://localhost:8000/health

# بررسی وضعیت MongoDB
docker exec telegram-mongodb mongosh \
  -u admin -p password \
  --eval "db.adminCommand('ping')"

# بررسی وضعیت Redis
docker exec telegram-redis redis-cli ping
```

## نکات مهم

1. ✅ تمام session_manager calls اکنون async هستند
2. ✅ SQLite و SQLAlchemy کاملا حذف شدند
3. ✅ MongoDB برای تمام داده‌ها استفاده می‌شود
4. ✅ Session files همچنان در filesystem ذخیره می‌شوند (برای Telethon)
5. ✅ Redis برای caching باقی مانده
6. ✅ تمام API endpoints بدون تغییر کار می‌کنند

## مراحل بعدی (اختیاری)

- [ ] نوشتن Unit Tests برای MongoDB operations
- [ ] اضافه کردن Monitoring (Prometheus/Grafana)
- [ ] پیاده‌سازی Rate Limiting
- [ ] اضافه کردن Logging به MongoDB
- [ ] پیاده‌سازی Backup خودکار

## مستندات بیشتر

- `docs.md` - مستندات کامل API
- `MONGODB_MIGRATION.md` - راهنمای مهاجرت به MongoDB
- `README.md` - راهنمای نصب و اجرا
