# Cynteka Dashboard

Streamlit дашборд для мониторинга заявок, счетов и доставок в системе Cynteka по проектам и ответственным сотрудникам.

## Функциональность

### Основные метрики
- Всего заявок (с динамикой за неделю)
- Заявки в работе (с процентом от общего числа)
- Закрытые в срок заявки (с процентом эффективности)
- Счета на согласовании

### Вкладки

1. **Заявки по проектам**
   - Таблица со статусами по каждому проекту
   - Процент закрытия в срок
   - График распределения статусов

2. **Счета на оплату**
   - Счета на согласовании с цветовой индикацией:
     - 🟢 < 3 дней — норма
     - 🟡 3-7 дней — внимание
     - 🔴 > 7 дней — критично
   - Общая сумма на согласовании

3. **Доставки**
   - Запланированные доставки
   - Фильтры: сегодня / на неделе / все
   - Адреса, поставщики, ответственные

4. **По сотрудникам**
   - Статистика по каждому ответственному
   - Эффективность (% закрытия в срок)
   - Топ-10 по загрузке

### Фильтры
- Период (по умолчанию: последние 30 дней)
- Проекты (множественный выбор)
- Ответственные (множественный выбор)
- Автообновление данных (каждые 5 минут)

## Установка и запуск

### 1. Клонирование репозитория

```bash
git clone https://github.com/Artemtru/cynteka-dashboard.git
cd cynteka-dashboard
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка API

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Получите API-токен Cynteka:
- **Телефон техподдержки**: 8-800-333-84-60
- **Email**: help@cynteka.ru
- **Документация**: http://wiki.cynteka.ru/docs/news

Запросите у администратора:
- Endpoint API (обычно `https://api.cynteka.ru` или URL вашей инсталляции)
- API-токен для доступа

Заполните `.env`:

```env
CYNTEKA_API_URL=https://api.cynteka.ru
CYNTEKA_API_TOKEN=your_actual_token_here
```

### 4. Запуск локально

```bash
streamlit run app.py
```

Дашборд откроется в браузере на `http://localhost:8501`

## Деплой на VPS

### Вариант 1: Docker (рекомендуется)

```bash
# Создать Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
EOF

# Собрать образ
docker build -t cynteka-dashboard .

# Запустить контейнер
docker run -d \
  --name cynteka-dashboard \
  -p 8501:8501 \
  --env-file .env \
  --restart unless-stopped \
  cynteka-dashboard
```

### Вариант 2: systemd service

```bash
# Создать systemd unit
sudo tee /etc/systemd/system/cynteka-dashboard.service > /dev/null << EOF
[Unit]
Description=Cynteka Dashboard
After=network.target

[Service]
Type=simple
User=hermes
WorkingDirectory=/opt/data/cynteka-dashboard
Environment="PATH=/opt/data/cynteka-dashboard/.venv/bin"
ExecStart=/opt/data/cynteka-dashboard/.venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Установить venv и зависимости
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Запустить сервис
sudo systemctl daemon-reload
sudo systemctl enable cynteka-dashboard
sudo systemctl start cynteka-dashboard
sudo systemctl status cynteka-dashboard
```

### Nginx reverse proxy

```nginx
server {
    listen 80;
    server_name cynteka.example.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Интеграция с реальным API Cynteka

После получения токена отредактируйте `cynteka_api.py`:

1. Замените заглушки на реальные запросы к API
2. Документация API обычно доступна в личном кабинете Cynteka
3. Типичные endpoints:
   - `/api/projects` — список проектов
   - `/api/users` — список сотрудников
   - `/api/requests` — заявки
   - `/api/invoices` — счета
   - `/api/deliveries` — доставки

Пример реального запроса:

```python
def get_projects(self) -> List[str]:
    response = self._get('projects')
    return [p['name'] for p in response['data']]
```

## TODO

- [ ] Получить API-токен Cynteka
- [ ] Реализовать реальные запросы к API вместо заглушек
- [ ] Добавить экспорт отчётов в Excel
- [ ] Добавить графики трендов
- [ ] Добавить уведомления о критичных просрочках
- [ ] Интеграция с Telegram для алертов

## Поддержка

- Официальная Wiki Cynteka: http://wiki.cynteka.ru/docs/news
- Техподдержка Cynteka: 8-800-333-84-60, help@cynteka.ru
- GitHub Issues: https://github.com/Artemtru/cynteka-dashboard/issues

## Лицензия

MIT
