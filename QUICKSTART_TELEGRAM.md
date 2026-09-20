# 🚀 Быстрый старт Telegram Mini App

## Что нужно сделать СЕЙЧАС

### 1️⃣ Создать бота в @BotFather (3 минуты)

Открыть **@BotFather** в Telegram:

```
/newbot
```

Ввести название: `Cynteka Dashboard`  
Ввести username: `CyntekaDashboard_bot` (или любой свободный на `bot`)

**Скопировать токен** → добавить в `.env` на VPS

---

### 2️⃣ Настроить Menu Button в @BotFather (1 минута)

```
/mybots
→ Выбрать своего бота
→ Bot Settings
→ Menu Button
→ Configure menu button
```

**Button name:** `📊 Dashboard`  
**Button URL:** `http://13.140.145.240:8501`

---

### 3️⃣ Узнать свой Telegram ID (30 секунд)

Написать **@userinfobot** в Telegram → скопировать ID (например `639180902`)

---

### 4️⃣ Обновить .env на VPS (2 минуты)

SSH на VPS и отредактировать конфиг:

```bash
ssh root@13.140.145.240
cd /opt/data/cynteka-dashboard
nano .env
```

Добавить строки:

```env
# Токен от @BotFather (шаг 1)
TELEGRAM_BOT_TOKEN=7123456789:AAE...

# Ваш ID от @userinfobot (шаг 3)
TELEGRAM_ALLOWED_USERS=639180902

# URL дашборда
WEBAPP_URL=http://13.140.145.240:8501

# Для теста можно включить
ALLOW_ANONYMOUS=false
```

Сохранить: `Ctrl+O`, `Enter`, `Ctrl+X`

---

### 5️⃣ Установить зависимости (1 минута)

```bash
cd /opt/data/cynteka-dashboard
source .venv/bin/activate
pip install python-telegram-bot>=21.0
```

---

### 6️⃣ Запустить бота (1 минута)

**Вариант A: Docker** (если Docker работает)

```bash
docker compose up -d
docker compose logs -f telegram-bot  # Проверка
```

**Вариант B: systemd** (если Docker не работает)

```bash
# Скопировать service файл
sudo cp cynteka-telegram-bot.service /etc/systemd/system/

# Запустить
sudo systemctl daemon-reload
sudo systemctl start cynteka-telegram-bot
sudo systemctl enable cynteka-telegram-bot

# Проверить
sudo systemctl status cynteka-telegram-bot
```

---

### 7️⃣ Протестировать! (30 секунд)

1. Найти своего бота в Telegram → `/start`
2. Нажать кнопку **"📊 Открыть Dashboard"**
3. Дашборд откроется **внутри Telegram**!

---

## 🔥 Если что-то не работает

### "Access denied" в боте
→ Проверьте `TELEGRAM_ALLOWED_USERS` в `.env` (должен быть ваш ID)

### Бот не отвечает
→ Проверьте токен: `TELEGRAM_BOT_TOKEN` в `.env`  
→ Логи: `sudo journalctl -u cynteka-telegram-bot -f`

### Дашборд не открывается
→ Проверьте Streamlit: `curl http://localhost:8501`  
→ Перезапуск: `sudo systemctl restart cynteka-dashboard`

### "Доступ запрещён" в дашборде
→ Временно включите `ALLOW_ANONYMOUS=true` для теста

---

## 📂 Файлы

- `TELEGRAM_MINI_APP.md` — полная документация
- `telegram_bot.py` — код бота
- `app.py` — Streamlit с авторизацией
- `cynteka-telegram-bot.service` — systemd конфиг

Коммит **5c968f1** уже в GitHub: https://github.com/Artemtru/cynteka-dashboard

---

**Время на запуск: ~10 минут**  
**Результат: полноценный дашборд прямо в Telegram!**

