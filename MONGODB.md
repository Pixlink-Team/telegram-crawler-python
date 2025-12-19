# راهنمای MongoDB

## 🗄️ نصب و راه‌اندازی MongoDB

### نصب MongoDB (Local)

#### macOS
```bash
brew tap mongodb/brew
brew install mongodb-community@7.0
brew services start mongodb-community@7.0
```

#### Ubuntu/Debian
```bash
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
```

#### Docker
```bash
docker run -d -p 27017:27017 --name telegram-mongodb mongo:7
```

### استفاده از Docker Compose (توصیه می‌شود)
```bash
docker-compose up -d
```

## 📊 دسترسی به MongoDB

### MongoDB Shell
```bash
# اتصال به MongoDB
mongosh

# انتخاب دیتابیس
use telegram_service

# مشاهده collections
show collections

# مشاهده تمام پیام‌ها
db.messages.find().pretty()

# مشاهده آخرین 10 پیام
db.messages.find().sort({date: -1}).limit(10)
```

### MongoDB Compass (GUI)
1. دانلود از: https://www.mongodb.com/try/download/compass
2. اتصال با: `mongodb://localhost:27017`
3. انتخاب دیتابیس: `telegram_service`

## 🔍 Query های مفید

### دریافت پیام‌های یک Agent
```javascript
db.messages.find({ 
  "agent_id": 123 
}).sort({ "date": -1 })
```

### جستجو در متن پیام‌ها
```javascript
db.messages.find({ 
  "text": { $regex: "سلام", $options: "i" } 
})
```

### پیام‌های یک چت خاص
```javascript
db.messages.find({ 
  "session_id": "your-session-id",
  "chat_id": 123456789 
}).sort({ "date": -1 })
```

### شمارش پیام‌ها
```javascript
db.messages.countDocuments({ "agent_id": 123 })
```

### آخرین پیام هر چت
```javascript
db.messages.aggregate([
  { $sort: { "date": -1 } },
  { $group: {
    _id: "$chat_id",
    lastMessage: { $first: "$$ROOT" }
  }}
])
```

### آمار پیام‌ها بر اساس تاریخ
```javascript
db.messages.aggregate([
  { $match: { "agent_id": 123 } },
  { $group: {
    _id: { 
      $dateToString: { format: "%Y-%m-%d", date: { $toDate: "$date" } }
    },
    count: { $sum: 1 }
  }},
  { $sort: { "_id": -1 } }
])
```

### پیام‌های ارسالی vs دریافتی
```javascript
db.messages.aggregate([
  { $match: { "agent_id": 123 } },
  { $group: {
    _id: "$is_outgoing",
    count: { $sum: 1 }
  }}
])
```

### فعال‌ترین چت‌ها
```javascript
db.messages.aggregate([
  { $match: { "agent_id": 123 } },
  { $group: {
    _id: "$chat_id",
    count: { $sum: 1 },
    lastMessage: { $last: "$text" }
  }},
  { $sort: { "count": -1 } },
  { $limit: 10 }
])
```

## 🔧 مدیریت و نگهداری

### Backup
```bash
# Backup کل دیتابیس
mongodump --db telegram_service --out /backup/

# Restore
mongorestore --db telegram_service /backup/telegram_service/
```

### Export به JSON
```bash
mongoexport --db telegram_service --collection messages --out messages.json
```

### Import از JSON
```bash
mongoimport --db telegram_service --collection messages --file messages.json
```

### پاک کردن پیام‌های قدیمی
```javascript
// پاک کردن پیام‌های بیشتر از 30 روز قبل
db.messages.deleteMany({
  "created_at": {
    $lt: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
  }
})
```

## 📈 بهینه‌سازی

### ایجاد Index
```javascript
// Index برای جستجوی سریع‌تر
db.messages.createIndex({ "text": "text" })

// Compound index
db.messages.createIndex({ "agent_id": 1, "date": -1 })
```

### مشاهده Indexes
```javascript
db.messages.getIndexes()
```

## 🔌 اتصال از Python

```python
from pymongo import MongoClient

# اتصال
client = MongoClient("mongodb://localhost:27017")
db = client.telegram_service

# دریافت پیام‌ها
messages = db.messages.find({"agent_id": 123}).limit(10)
for msg in messages:
    print(msg['text'])

# ذخیره پیام
db.messages.insert_one({
    "agent_id": 123,
    "session_id": "uuid",
    "text": "Hello",
    "created_at": datetime.utcnow()
})
```

## 🛠️ Troubleshooting

### مشکل: MongoDB راه‌اندازی نمی‌شود
```bash
# بررسی وضعیت
sudo systemctl status mongod

# مشاهده logs
sudo tail -f /var/log/mongodb/mongod.log
```

### مشکل: خطای اتصال
```bash
# بررسی پورت
netstat -an | grep 27017

# تست اتصال
mongosh --eval "db.adminCommand('ping')"
```

### مشکل: فضای دیسک کم
```bash
# بررسی فضای استفاده شده
du -sh /var/lib/mongodb

# فشرده‌سازی دیتابیس
db.runCommand({ compact: 'messages' })
```

## 📚 منابع مفید

- [MongoDB Documentation](https://docs.mongodb.com/)
- [MongoDB University (رایگان)](https://university.mongodb.com/)
- [Aggregation Pipeline](https://docs.mongodb.com/manual/core/aggregation-pipeline/)
- [Query Operators](https://docs.mongodb.com/manual/reference/operator/query/)

## 💡 نکات مهم

1. ✅ همیشه از Index استفاده کنید برای query های پرتکرار
2. ✅ Backup منظم از دیتابیس بگیرید
3. ✅ از Aggregation Pipeline برای آنالیزهای پیچیده استفاده کنید
4. ✅ پیام‌های قدیمی را آرشیو یا حذف کنید
5. ✅ از MongoDB Compass برای دیدن بصری داده‌ها استفاده کنید

---

برای سوالات بیشتر، به [docs.mongodb.com](https://docs.mongodb.com) مراجعه کنید.
