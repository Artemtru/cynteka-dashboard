# Telegram Mini App — инструкция по настройке

## Что уже сделано

✅ Telegram бот (`telegram_bot.py`) с командами `/start`, `/stats`, `/help`  
✅ Авторизация в Streamlit через URL параметры от бота  
✅ Кнопка "Открыть Dashboard" — открывает Streamlit прямо в Telegram  
✅ Белый список пользователей (контроль доступа через `.env`)

---

## Шаг 1: Создание бота в Telegram

1. Откройте **@BotFather** в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям:
   - Введите **название бота**, например: `Cynteka Dashboard`
   - Введите **username бота** (должен заканчиваться на `bot`), например: `CyntekaDashboard_bot`
4. **Скопируйте токен** — вида `7123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw`
5. **Настройте Web App**:
   ```
   /mybots
   @CyntekaDashboard_bot (выберите вашего бота)
   Bot Settings
   Menu Button
   Configure menu button
   ```
   - **Button name:** `📊 Dashboard`
   - **Button URL:** `http://13.140.145.240:8501` (URL где запущен Streamlit)

---

## Шаг 2: Настройка переменных окружения

Отредактируйте файл `.env` на VPS:

```bash
# От admin с VPS
ssh root@13.140.145.240
cd /opt/data/cynteka-dashboard
nano .env
```

Добавьте/обновите:

```env
# Cynteka API (получите у админа)
CYNTEKA_API_URL=https://anvaz.cynteka.ru/api/v1
CYNTEKA_API_TOKEN=ваш_токен_из_dashboard

# Telegram Bot
TELEGRAM_BOT_TOKEN=7123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw
TELEGRAM_ALLOWED_USERS=639180902,123456789
# ↑ Ваши Telegram ID через запятую (узнать свой ID: @userinfobot)

# Streamlit Web App URL
WEBAPP_URL=http://13.140.145.240:8501

# Development (для тестирования БЕЗ Telegram)
ALLOW_ANONYMOUS=false  # true — разрешит доступ без бота (ТОЛЬКО для разработки!)
```

Сохраните: `Ctrl+O`, `Enter`, `Ctrl+X`

---

## Шаг 3: Установка зависимостей

```bash
cd /opt/data/cynteka-dashboard
source .venv/bin/activate

# Установка python-telegram-bot
pip install python-telegram-bot>=21.0
```

---

## Шаг 4: Запуск сервисов

### Вариант A: Docker Compose (рекомендуется)

Обновим `docker-compose.yml`:

```yaml
version: '3.8'

services:
  dashboard:
    build: .
    ports:
      - "8501:8501"
    env_file:
      - .env
    restart: unless-stopped
    volumes:
      - ./:/app
    command: streamlit run app.py --server.port=8501 --server.address=0.0.0.0

  telegram-bot:
    build: .
    env_file:
      - .env
    restart: unless-stopped
    depends_on:
      - dashboard
    command: python telegram_bot.py
```

Запуск:

```bash
docker compose up -d
docker compose logs -f  # Проверка логов
```

### Вариант B: systemd сервисы (если Docker не работает)

**1. Streamlit Dashboard**

Используйте существующий `cynteka-dashboard.service`:

```bash
sudo systemctl start cynteka-dashboard
sudo systemctl status cynteka-dashboard
```

**2. Telegram Bot**

Создайте `/etc/systemd/system/cynteka-bot.service`:

```ini
[Unit]
Description=Cynteka Telegram Bot
After=network.target cynteka-dashboard.service

[Service]
Type=simple
User=hermes
WorkingDirectory=/opt/data/cynteka-dashboard
Environment="PATH=/opt/data/cynteka-dashboard/.venv/bin"
ExecStart=/opt/data/cynteka-dashboard/.venv/bin/python telegram_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Запуск:

```bash
sudo systemctl daemon-reload
sudo systemctl start cynteka-bot
sudo systemctl enable cynteka-bot
sudo systemctl status cynteka-bot
```

---

## Шаг 5: Проверка работы

### 1. Проверьте Streamlit

Откройте в браузере: `http://13.140.145.240:8501`

- Должна появиться ошибка **"Доступ запрещён"** (это нормально — работает авторизация)
- Для теста можете временно включить `ALLOW_ANONYMOUS=true` в `.env` и перезапустить

### 2. Проверьте бота

1. Найдите вашего бота в Telegram → `/start`
2. Должна появиться **кнопка "📊 Открыть Dashboard"**
3. Нажмите на неё — откроется дашборд **внутри Telegram**
4. В sidebar должно быть: `👤 ВашUsername`

### 3. Логи (если что-то не работает)

```bash
# Streamlit
tail -f streamlit.log

# Telegram bot (если systemd)
sudo journalctl -u cynteka-bot -f

# Docker
docker compose logs -f telegram-bot
```

---

## Что делать, если не работает

### Ошибка: "Доступ запрещён" в боте

**Причина:** Ваш Telegram ID не в `TELEGRAM_ALLOWED_USERS`

**Решение:**
1. Узнайте свой ID → напишите @userinfobot в Telegram
2. Добавьте ID в `.env`: `TELEGRAM_ALLOWED_USERS=639180902,ВАШ_ID`
3. Перезапустите бота

### Ошибка: "Bad credentials" в логах бота

**Причина:** Неверный `TELEGRAM_BOT_TOKEN`

**Решение:**
1. Проверьте токен в `.env` (без пробелов)
2. Создайте нового бота через @BotFather если потеряли токен

### Дашборд не открывается в Telegram

**Причина:** Неверный `WEBAPP_URL` или Streamlit не запущен

**Решение:**
```bash
# Проверьте порт 8501
curl http://localhost:8501

# Перезапустите Streamlit
sudo systemctl restart cynteka-dashboard

# Обновите URL в @BotFather → Menu Button
```

### Дашборд открывается но показывает "Доступ запрещён"

**Причина:** URL параметры не передаются от бота

**Решение:**
1. Проверьте что в `telegram_bot.py` строка:
   ```python
   url=f"{WEBAPP_URL}?tg_user_id={user_id}&tg_username={user.username}"
   ```
2. Временно включите `ALLOW_ANONYMOUS=true` для теста

---

## Дополнительные команды

### Узнать свой Telegram ID
Напишите @userinfobot в Telegram

### Добавить второго пользователя
```bash
nano .env
# Добавьте ID через запятую:
TELEGRAM_ALLOWED_USERS=639180902,987654321
```

### Просмотреть логи бота в реальном времени
```bash
sudo journalctl -u cynteka-bot -f --lines=50
```

### Перезапустить всё
```bash
# Docker
docker compose restart

# systemd
sudo systemctl restart cynteka-dashboard cynteka-bot
```

---

## Roadmap (что можно добавить)

- [ ] Уведомления о просрочках (функция `send_overdue_alerts` в боте)
- [ ] Команда `/export` — выгрузка отчёта в Excel
- [ ] Inline-кнопки в `/stats` для быстрых фильтров
- [ ] Webhook уведомления от Cynteka API (вместо polling)
- [ ] Админская панель для управления доступами

---

## Контакты

- **Техподдержка Cynteka:** 8-800-333-84-60, help@cynteka.ru
- **API документация:** [Cynteka API Docs](https://anvaz.cynteka.ru/api/docs)
- **GitHub репозиторий:** Artemtru/cynteka-dashboard

