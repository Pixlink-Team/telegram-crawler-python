# MongoDB Migration Guide

## تغییرات انجام شده

### حذف SQLite و SQLAlchemy
- تمام وابستگی‌های SQLAlchemy، Alembic و aiosqlite حذف شدند
- فایل `alembic.ini` و پوشه `app/models` حذف شدند
- متغیر محیطی `DATABASE_URL` از تمام فایل‌های config حذف شد

### استفاده از MongoDB برای همه داده‌ها
اکنون تمام داده‌ها در MongoDB ذخیره می‌شوند:

1. **پیام‌ها** - Collection: `messages`
2. **رویدادها** - Collection: `events`
3. **اطلاعات Session** - Collection: `telegram_sessions`

### ساختار Collection های MongoDB

#### telegram_sessions
```json
{
  "_id": "ObjectId",
  "agent_id": 123,
  "session_id": "uuid-string",
  "session_file": "session_file_name",
  "phone": "+989123456789",
  "user_id": 123456789,
  "is_active": true,
  "connected_at": "2024-01-01T00:00:00",
  "last_activity": "2024-01-01T00:00:00",
  "metadata": {},
  "created_at": "2024-01-01T00:00:00"
}
```

#### messages
```json
{
  "_id": "ObjectId",
  "session_id": "uuid-string",
  "agent_id": 123,
  "message_id": 123,
  "chat_id": 456,
  "sender_id": 789,
  "text": "message text",
  "date": "2024-01-01T00:00:00",
  "is_outgoing": false,
  "media_type": "photo",
  "reply_to_msg_id": null,
  "metadata": {},
  "created_at": "2024-01-01T00:00:00"
}
```

#### events
```json
{
  "_id": "ObjectId",
  "session_id": "uuid-string",
  "agent_id": 123,
  "event_type": "message.new",
  "chat_id": 456,
  "data": {},
  "created_at": "2024-01-01T00:00:00"
}
```

## تغییرات کد

### SessionManager
فایل `app/utils/session_manager.py` به طور کامل بازنویسی شد:
- تمام متدها اکنون `async` هستند
- به جای SQLAlchemy از MongoDB استفاده می‌کند
- به جای مدل‌های SQLAlchemy، dictionary برمی‌گرداند

قبل:
```python
session = session_manager.get_session_by_id(session_id)
phone = session.phone
```

بعد:
```python
session = await session_manager.get_session_by_id(session_id)
phone = session.get("phone")
```

### تغییرات در Routes
تمام فراخوانی‌های `session_manager` در `app/api/routes.py` به `async/await` تبدیل شدند:
- `session_manager.method()` → `await session_manager.method()`
- دسترسی به فیلدها: `session.field` → `session.get("field")` یا `session["field"]`

### MongoDB Service
سرویس جامع MongoDB در `app/services/mongodb.py` افزوده شد با قابلیت‌های:
- مدیریت پیام‌ها و رویدادها
- مدیریت session ها
- آمار و گزارش‌گیری
- ساخت index های بهینه

## اجرای پروژه

### 1. تنظیم متغیرهای محیطی
فایل `.env`:
```env
# MongoDB
MONGODB_URI=mongodb://admin:password@mongodb:27017
MONGODB_DB=telegram_crawler

# Redis
REDIS_URL=redis://redis:6379/0

# Telegram API
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

# Security
API_SECRET_KEY=your-secret-key-here
```

### 2. اجرا با Docker Compose
```bash
docker-compose up -d
```

سرویس‌های زیر اجرا می‌شوند:
- `app`: سرویس FastAPI (پورت 8000)
- `mongodb`: MongoDB (پورت 27017)
- `redis`: Redis (پورت 6379)

### 3. بررسی لاگ‌ها
```bash
docker-compose logs -f app
```

### 4. دسترسی به MongoDB
```bash
docker exec -it telegram-mongodb mongosh -u admin -p password
```

## API Endpoints

همه endpoint ها بدون تغییر باقی مانده‌اند:
- `POST /request-qr` - درخواست QR Code
- `POST /request-phone-code` - درخواست کد با شماره
- `POST /verify-code` - تایید کد
- `POST /verify-password` - تایید رمز عبور
- `POST /disconnect` - قطع اتصال
- `GET /status/{session_id}` - وضعیت session
- `POST /send-message` - ارسال پیام
- `GET /messages` - دریافت پیام‌ها
- `GET /chat-history/{session_id}/{chat_id}` - تاریخچه چت
- `GET /agent-stats/{agent_id}` - آمار agent

## تست API

```bash
# درخواست QR Code
curl -X POST http://localhost:8000/request-qr \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": 1}'

# دریافت پیام‌ها
curl -X GET "http://localhost:8000/messages?session_id=xxx&limit=10" \
  -H "X-API-Key: your-api-key"
```

## مزایای MongoDB نسبت به SQLite

1. **مقیاس‌پذیری**: بهتر برای حجم بالای داده
2. **کارایی**: Index های بهینه برای query های سریع
3. **انعطاف‌پذیری**: Schema انعطاف‌پذیر برای metadata
4. **توزیع**: قابلیت توزیع در چند سرور
5. **یکپارچگی**: یک دیتابیس برای تمام داده‌ها

## نکات مهم

1. **Session Files**: فایل‌های session همچنان در `/app/sessions` ذخیره می‌شوند (برای Telethon)
2. **Redis**: همچنان برای caching استفاده می‌شود
3. **Async**: تمام عملیات MongoDB و session_manager اکنون async هستند
4. **Dictionary Access**: session records اکنون dictionary هستند نه SQLAlchemy model

## Backup و Restore

### Backup
```bash
docker exec telegram-mongodb mongodump \
  -u admin -p password \
  --db telegram_crawler \
  --out /backup
```

### Restore
```bash
docker exec telegram-mongodb mongorestore \
  -u admin -p password \
  --db telegram_crawler \
  /backup/telegram_crawler
```
