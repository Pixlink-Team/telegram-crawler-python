# مستندات سرویس تلگرام (پایتون)

## 📋 خلاصه پروژه
یک سرویس مستقل پایتون که:
- به تلگرام متصل می‌شود (با استفاده از Telethon یا Pyrogram)
- QR Code و کد تایید را مدیریت می‌کند
- پیام‌های دریافتی از تلگرام را به Laravel Backend ارسال می‌کند
- Session های متعدد Agent ها را همزمان مدیریت می‌کند

---

## 🎯 وظایف اصلی سرویس

### 1. مدیریت اتصال تلگرام
- دریافت درخواست اتصال از Agent ها
- ایجاد Session جدید برای هر Agent
- تولید QR Code یا درخواست کد تایید
- ذخیره و مدیریت Session ها

### 2. دریافت و ارسال پیام‌ها
- دریافت تمام پیام‌های تلگرام برای هر Agent
- ارسال پیام‌های تلگرام از طرف Agent
- Webhook به Laravel برای اطلاع‌رسانی پیام جدید

### 3. مدیریت Session
- نگهداری Session های فعال
- Reconnect خودکار در صورت قطع اتصال
- Logout و حذف Session

---

## 🔌 API Endpoints که باید پیاده‌سازی شوند

### 1. **POST /api/telegram/request-qr**
درخواست شروع فرآیند اتصال

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

**توضیحات:**
- ایجاد یک Session جدید برای Agent
- تولید QR Code با استفاده از Telethon
- QR Code باید Base64 encoded باشه
- Session ID منحصر به فرد برای پیگیری

---

### 2. **POST /api/telegram/verify-code**
تایید کد دریافتی از تلگرام

**Request:**
```json
{
  "session_id": "uuid-v4-session-id",
  "code": "12345"
}
```

**Response (موفق):**
```json
{
  "success": true,
  "connected": true,
  "phone": "+989123456789",
  "user_id": 123456789
}
```

**Response (نیاز به Password):**
```json
{
  "success": true,
  "connected": false,
  "requires_password": true
}
```

**Response (خطا):**
```json
{
  "success": false,
  "error": "کد نامعتبر است"
}
```

---

### 3. **POST /api/telegram/verify-password**
برای اکانت‌هایی که 2FA دارند

**Request:**
```json
{
  "session_id": "uuid-v4-session-id",
  "password": "my-password"
}
```

**Response:**
```json
{
  "success": true,
  "connected": true,
  "phone": "+989123456789",
  "user_id": 123456789
}
```

---

### 4. **POST /api/telegram/disconnect**
قطع اتصال و حذف Session

**Request:**
```json
{
  "session_id": "uuid-v4-session-id"
}
```

**Response:**
```json
{
  "success": true,
  "message": "اتصال با موفقیت قطع شد"
}
```

---

### 5. **GET /api/telegram/status/{session_id}**
بررسی وضعیت اتصال

**Response:**
```json
{
  "success": true,
  "connected": true,
  "phone": "+989123456789",
  "user_id": 123456789,
  "last_activity": "2025-12-20T10:30:00Z"
}
```

---

### 6. **POST /api/telegram/send-message**
ارسال پیام از طریق تلگرام

**Request:**
```json
{
  "session_id": "uuid-v4-session-id",
  "chat_id": 123456789,
  "message": "سلام، چطور می‌تونم کمکتون کنم؟",
  "reply_to": null
}
```

**Response:**
```json
{
  "success": true,
  "message_id": 987654321,
  "sent_at": "2025-12-20T10:30:00Z"
}
```

---

## 🔗 Webhook به Laravel Backend

سرویس پایتون باید وقتی پیام جدیدی دریافت می‌شه، به Laravel اطلاع بده.

### **POST {LARAVEL_BASE_URL}/api/webhooks/telegram/{agent_id}**

**Headers:**
```
Authorization: Bearer {WEBHOOK_SECRET_TOKEN}
Content-Type: application/json
```

**Request Body:**
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
    "text": "سلام، می‌خوام محصولتون رو بخرم",
    "date": "2025-12-20T10:30:00Z",
    "reply_to_message_id": null
  }
}
```

**Event Types:**
- `new_message`: پیام جدید
- `message_edited`: ویرایش پیام
- `session_expired`: Session منقضی شده
- `connection_lost`: قطع اتصال
- `connection_restored`: اتصال مجدد

---

## 🏗️ معماری پیشنهادی

### Stack تکنولوژی:
- **Python 3.11+**
- **FastAPI**: برای REST API
- **Telethon یا Pyrogram**: برای اتصال به تلگرام
- **PostgreSQL یا SQLite**: ذخیره Session ها
- **Redis**: Cache و Queue مدیریت
- **Docker**: برای Deploy

### ساختار پروژه پیشنهادی:
```
telegram-service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py               # تنظیمات
│   ├── models/
│   │   ├── __init__.py
│   │   └── session.py          # Session model
│   ├── services/
│   │   ├── __init__.py
│   │   ├── telegram.py         # Telegram client management
│   │   └── webhook.py          # Laravel webhook sender
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py           # API endpoints
│   │   └── schemas.py          # Pydantic schemas
│   └── utils/
│       ├── __init__.py
│       ├── qr_generator.py     # QR code generator
│       └── session_manager.py  # Session management
├── tests/
├── sessions/                   # Telegram session files
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## ⚙️ تنظیمات محیطی (Environment Variables)

```env
# Telegram API
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=False

# Database
DATABASE_URL=sqlite:///./sessions.db
# یا برای PostgreSQL:
# DATABASE_URL=postgresql://user:pass@localhost/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# Laravel Backend
LARAVEL_BASE_URL=http://localhost:8000
WEBHOOK_SECRET_TOKEN=your-secret-token-here

# Security
API_SECRET_KEY=your-secret-key-for-api-auth
```

---

## 🔒 امنیت

### 1. Authentication
- تمام API endpoints باید با API Key محافظت شوند
- Laravel Backend باید توکن معتبر داشته باشد

### 2. Session Storage
- Session files باید رمزنگاری شوند
- دسترسی به فایل‌های Session محدود باشد

### 3. Webhook Security
- استفاده از HTTPS برای Webhook ها
- امضای دیجیتال برای Webhook payloads

---

## 📦 Dependencies اصلی (requirements.txt)

```txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
telethon>=1.33.0
# یا
# pyrogram>=2.0.0

sqlalchemy>=2.0.0
alembic>=1.12.0
redis>=5.0.0
python-dotenv>=1.0.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
httpx>=0.25.0
qrcode[pil]>=7.4.0
cryptography>=41.0.0
python-multipart>=0.0.6
```

---

## 🚀 مراحل اجرا

### 1. راه‌اندازی اولیه
```bash
# کلون و نصب
git clone <repo>
cd telegram-service
python -m venv venv
source venv/bin/activate  # یا venv\Scripts\activate در Windows
pip install -r requirements.txt

# تنظیم Environment Variables
cp .env.example .env
# ویرایش .env و تنظیم مقادیر
```

### 2. دریافت Telegram API Credentials
- رفتن به https://my.telegram.org
- ساخت Application جدید
- کپی کردن API_ID و API_HASH

### 3. اجرای سرویس
```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production با Docker
docker-compose up -d
```

---

## 🧪 تست‌ها

### تست‌های مورد نیاز:
1. ✅ اتصال به تلگرام با QR Code
2. ✅ اتصال با Phone Code
3. ✅ مدیریت چند Session همزمان
4. ✅ دریافت و ارسال پیام
5. ✅ Webhook به Laravel
6. ✅ Reconnection خودکار
7. ✅ Logout و حذف Session

---

## 📊 مانیتورینگ و Logging

### Logs مورد نیاز:
- اتصالات جدید
- پیام‌های ارسالی/دریافتی
- خطاها و Exceptions
- وضعیت Session ها

### Metrics:
- تعداد Session های فعال
- تعداد پیام‌های پردازش شده
- زمان پاسخ‌دهی API
- میزان استفاده از منابع

---

## 🔄 مدیریت Session ها

### نکات مهم:
1. هر Agent یک Session منحصر به فرد دارد
2. Session files باید پایدار باشند (در Volume ذخیره شوند)
3. پس از Restart سرویس، Session ها باید بازیابی شوند
4. Session های غیرفعال پس از N روز حذف شوند

### Structure Session در Database:
```python
class TelegramSession:
    id: UUID
    agent_id: int
    session_id: str
    phone: str
    user_id: int
    is_active: bool
    connected_at: datetime
    last_activity: datetime
    session_file: str  # path to session file
    metadata: dict
```

---

## 🐛 مدیریت خطاها

### خطاهای رایج:
1. **FloodWaitError**: محدودیت تعداد درخواست به تلگرام
2. **SessionExpiredError**: Session منقضی شده
3. **PhoneCodeInvalidError**: کد نامعتبر
4. **PasswordHashInvalidError**: رمز نامعتبر
5. **NetworkError**: مشکل اتصال به اینترنت

### رفتار مورد انتظار:
- Retry با Exponential Backoff
- اطلاع‌رسانی به Laravel از طریق Webhook
- Logging جامع

---

## 📝 نکات تکمیلی

### قابلیت‌های اضافی (Nice to Have):
1. پشتیبانی از ارسال فایل، عکس، ویدیو
2. مدیریت گروه‌ها و کانال‌ها
3. دریافت اطلاعات مخاطب
4. جستجو در پیام‌ها
5. آرشیو پیام‌ها

### Scalability:
- استفاده از Celery برای پردازش Async
- Load Balancing برای چند Instance
- شاخت Cluster برای Session های زیاد

---

## 🔗 لینک‌های مفید

- [Telethon Documentation](https://docs.telethon.dev/)
- [Pyrogram Documentation](https://docs.pyrogram.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Telegram API Documentation](https://core.telegram.org/api)

---

## ✅ Checklist پیاده‌سازی

- [ ] Setup پروژه و ساختار اولیه
- [ ] پیاده‌سازی FastAPI endpoints
- [ ] اتصال به Telegram با Telethon
- [ ] مدیریت Session ها
- [ ] تولید QR Code
- [ ] مدیریت Phone Code و Password
- [ ] پیاده‌سازی Webhook به Laravel
- [ ] مدیریت پیام‌های دریافتی
- [ ] ارسال پیام به تلگرام
- [ ] Error Handling و Retry Logic
- [ ] Logging و Monitoring
- [ ] تست‌های Unit و Integration
- [ ] Dockerization
- [ ] مستندات API (Swagger/OpenAPI)
- [ ] Deploy و CI/CD

---

## 💡 مثال استفاده

### Python Client Example:
```python
import httpx

# درخواست QR Code
response = httpx.post(
    "http://localhost:8000/api/telegram/request-qr",
    json={"agent_id": 123},
    headers={"X-API-Key": "your-api-key"}
)
data = response.json()
print(f"QR Code: {data['qr_code']}")
print(f"Session ID: {data['session_id']}")

# تایید کد
response = httpx.post(
    "http://localhost:8000/api/telegram/verify-code",
    json={
        "session_id": data['session_id'],
        "code": "12345"
    },
    headers={"X-API-Key": "your-api-key"}
)
print(response.json())
```

---

**تاریخ ایجاد:** 2025-12-20  
**نسخه:** 1.0.0  
**وضعیت:** در انتظار پیاده‌سازی
