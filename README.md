# 📱 Telegram Service (Python)

یک سرویس مستقل پایتون برای مدیریت اتصالات و پیام‌های تلگرام با استفاده از Telethon

## ✨ ویژگی‌ها

- 🔐 اتصال به تلگرام با QR Code
- 📱 پشتیبانی از Phone Code و 2FA
- 💬 دریافت و ارسال پیام‌های تلگرام
- 🔄 مدیریت Session های متعدد به صورت همزمان
- 🪝 Webhook به Laravel Backend
- 🔌 Reconnect خودکار
- 🐳 Docker Support
- 📊 RESTful API با FastAPI

## 📋 پیش‌نیازها

- Python 3.11+
- Telegram API Credentials (API ID & API Hash)
- Redis (اختیاری)
- Docker & Docker Compose (برای deployment)

## 🚀 نصب و راه‌اندازی

### 1. دریافت Telegram API Credentials

1. به https://my.telegram.org بروید
2. وارد شوید و به قسمت "API development tools" بروید
3. یک Application جدید بسازید
4. API ID و API Hash را کپی کنید

### 2. نصب به صورت Local

```bash
# کلون پروژه
git clone <repository-url>
cd telegram-crawler-python

# ایجاد virtual environment
python -m venv venv
source venv/bin/activate  # در Windows: venv\Scripts\activate

# نصب dependencies
pip install -r requirements.txt

# کپی و تنظیم environment variables
cp .env.example .env
# ویرایش .env و تنظیم مقادیر
```

### 3. تنظیم فایل .env

```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
HOST=0.0.0.0
PORT=8000
DEBUG=False
DATABASE_URL=sqlite:///./sessions.db
REDIS_URL=redis://localhost:6379/0
LARAVEL_BASE_URL=http://your-laravel-backend.com
WEBHOOK_SECRET_TOKEN=your-secret-token
API_SECRET_KEY=your-api-secret-key
```

### 4. اجرای سرویس

#### روش اول: اجرای مستقیم

```bash
python -m app.main
# یا
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### روش دوم: Docker

```bash
# Build و اجرا
docker-compose up -d

# مشاهده logs
docker-compose logs -f

# متوقف کردن
docker-compose down
```

## 📖 استفاده از API

### Base URL
```
http://localhost:8000
```

### Authentication
تمام درخواست‌ها نیاز به API Key دارند که باید در header ارسال شود:
```
X-API-Key: your-api-secret-key
```

### Endpoints

#### 1. درخواست QR Code

```bash
POST /api/telegram/request-qr
```

**Request:**
```json
{
  "agent_id": 123
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "uuid-v4-session-id",
  "qr_code": "data:image/png;base64,iVBORw0KG...",
  "expires_in": 300
}
```

#### 2. تایید کد

```bash
POST /api/telegram/verify-code
```

**Request:**
```json
{
  "session_id": "uuid-v4-session-id",
  "code": "12345"
}
```

#### 3. تایید رمز عبور (2FA)

```bash
POST /api/telegram/verify-password
```

**Request:**
```json
{
  "session_id": "uuid-v4-session-id",
  "password": "my-password"
}
```

#### 4. قطع اتصال

```bash
POST /api/telegram/disconnect
```

**Request:**
```json
{
  "session_id": "uuid-v4-session-id"
}
```

#### 5. بررسی وضعیت

```bash
GET /api/telegram/status/{session_id}
```

#### 6. ارسال پیام

```bash
POST /api/telegram/send-message
```

**Request:**
```json
{
  "session_id": "uuid-v4-session-id",
  "chat_id": 123456789,
  "message": "سلام، چطور می‌تونم کمکتون کنم؟",
  "reply_to": null
}
```

### مثال استفاده با cURL

```bash
# درخواست QR Code
curl -X POST "http://localhost:8000/api/telegram/request-qr" \
  -H "X-API-Key: your-api-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": 123}'

# بررسی وضعیت
curl -X GET "http://localhost:8000/api/telegram/status/{session_id}" \
  -H "X-API-Key: your-api-secret-key"

# ارسال پیام
curl -X POST "http://localhost:8000/api/telegram/send-message" \
  -H "X-API-Key: your-api-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "uuid",
    "chat_id": 123456789,
    "message": "سلام"
  }'
```

### مثال استفاده با Python

```python
import httpx

API_BASE_URL = "http://localhost:8000"
API_KEY = "your-api-secret-key"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# درخواست QR Code
response = httpx.post(
    f"{API_BASE_URL}/api/telegram/request-qr",
    json={"agent_id": 123},
    headers=headers
)
data = response.json()
print(f"Session ID: {data['session_id']}")
print(f"QR Code: {data['qr_code']}")
```

## 🪝 Webhook به Laravel

سرویس پایتون به صورت خودکار برای رویدادهای زیر به Laravel Webhook ارسال می‌کند:

```
POST {LARAVEL_BASE_URL}/api/webhooks/telegram/{agent_id}
```

**Headers:**
```
Authorization: Bearer {WEBHOOK_SECRET_TOKEN}
Content-Type: application/json
```

**Event Types:**
- `new_message`: پیام جدید
- `message_edited`: ویرایش پیام
- `session_expired`: Session منقضی شده
- `connection_lost`: قطع اتصال
- `connection_restored`: اتصال مجدد

**مثال Payload:**
```json
{
  "event": "new_message",
  "session_id": "uuid-v4-session-id",
  "message": {
    "id": 123456,
    "from": {
      "id": 987654321,
      "first_name": "علی",
      "last_name": "محمدی",
      "username": "ali_m",
      "phone": "+989123456789"
    },
    "chat": {
      "id": 987654321,
      "type": "private"
    },
    "text": "سلام",
    "date": "2025-12-20T10:30:00Z",
    "reply_to_message_id": null
  }
}
```

## 📁 ساختار پروژه

```
telegram-crawler-python/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # تنظیمات
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py        # API endpoints
│   │   └── schemas.py       # Pydantic schemas
│   ├── models/
│   │   ├── __init__.py
│   │   └── session.py       # Database models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── telegram.py      # Telegram client management
│   │   └── webhook.py       # Webhook sender
│   └── utils/
│       ├── __init__.py
│       ├── qr_generator.py  # QR code generator
│       └── session_manager.py # Session management
├── sessions/                # Session files
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── docs.md                  # مستندات کامل
└── README.md               # این فایل
```

## 🔧 توسعه و تست

### اجرای در حالت Development

```bash
# با reload خودکار
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### مشاهده Swagger UI

پس از اجرای سرویس، به آدرس زیر بروید:
```
http://localhost:8000/docs
```

### مشاهده ReDoc

```
http://localhost:8000/redoc
```

## 🐛 عیب‌یابی

### مشکلات رایج

1. **خطای "Session not found"**
   - مطمئن شوید session_id صحیح است
   - بررسی کنید که Session در دیتابیس موجود باشد

2. **خطای "Invalid API key"**
   - API_SECRET_KEY در .env را بررسی کنید
   - Header X-API-Key را در درخواست قرار دهید

3. **خطای "FloodWaitError"**
   - تلگرام محدودیت تعداد درخواست دارد
   - چند دقیقه صبر کنید و دوباره تلاش کنید

4. **Session منقضی می‌شود**
   - Session files را backup کنید
   - از Volume در Docker استفاده کنید

### مشاهده Logs

```bash
# Docker
docker-compose logs -f telegram-service

# Local
# Logs در console نمایش داده می‌شوند
```

## 📊 Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "active_sessions": 5
}
```

## 🔒 امنیت

### توصیه‌های امنیتی

1. ✅ API_SECRET_KEY قوی استفاده کنید
2. ✅ HTTPS برای Production
3. ✅ محدود کردن CORS
4. ✅ Firewall برای محدود کردن دسترسی
5. ✅ Backup منظم از Session files
6. ✅ استفاده از Environment Variables

### محدود کردن CORS (Production)

در فایل [app/main.py](app/main.py):

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## 🚢 Deployment

### Docker Production

```bash
# Build image
docker build -t telegram-service:latest .

# Run container
docker run -d \
  --name telegram-service \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/sessions:/app/sessions \
  telegram-service:latest
```

### با Docker Compose

```bash
docker-compose -f docker-compose.yml up -d
```

## 📝 Changelog

### Version 1.0.0 (2025-12-20)
- ✅ پیاده‌سازی اولیه
- ✅ اتصال به تلگرام با QR Code
- ✅ مدیریت Session ها
- ✅ دریافت و ارسال پیام
- ✅ Webhook به Laravel
- ✅ Docker Support

## 🤝 مشارکت

برای مشارکت در پروژه:

1. Fork کنید
2. یک Branch جدید بسازید (`git checkout -b feature/AmazingFeature`)
3. تغییرات را Commit کنید (`git commit -m 'Add some AmazingFeature'`)
4. Push کنید (`git push origin feature/AmazingFeature`)
5. یک Pull Request باز کنید

## 📄 License

این پروژه تحت لایسنس MIT است.

## 📞 پشتیبانی

برای سوالات و مشکلات، Issue باز کنید یا به تیم توسعه مراجعه کنید.

## 🔗 لینک‌های مفید

- [Telethon Documentation](https://docs.telethon.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Telegram API Documentation](https://core.telegram.org/api)
- [مستندات کامل پروژه](docs.md)

---

**ساخته شده با ❤️ برای Laravel Backend Integration**
