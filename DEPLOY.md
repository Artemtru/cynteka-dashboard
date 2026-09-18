# 🚀 Инструкция по деплою Cynteka Dashboard на VPS

## Вариант 1: Systemd сервис (рекомендуется)

Выполните **на хосте VPS** (не внутри Docker контейнера):

```bash
# 1. Создать systemd service
sudo tee /etc/systemd/system/cynteka-dashboard.service > /dev/null << 'EOF'
[Unit]
Description=Cynteka Dashboard
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/data/cynteka-dashboard
Environment="PATH=/opt/data/cynteka-dashboard/.venv/bin"
ExecStart=/opt/data/cynteka-dashboard/.venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 2. Запустить сервис
sudo systemctl daemon-reload
sudo systemctl enable cynteka-dashboard
sudo systemctl start cynteka-dashboard

# 3. Проверить статус
sudo systemctl status cynteka-dashboard

# 4. Проверить доступность
curl http://localhost:8501/_stcore/health
```

Дашборд будет доступен по адресу:
- **Внутри VPS**: http://localhost:8501
- **Снаружи**: http://13.140.145.240:8501

---

## Вариант 2: Docker контейнер

Если нужно запустить через Docker:

```bash
# 1. Включить Docker daemon на хосте
sudo systemctl start docker

# 2. Перейти в директорию проекта
cd /opt/data/cynteka-dashboard

# 3. Собрать и запустить контейнер
docker build -t cynteka-dashboard .
docker run -d \
  --name cynteka-dashboard \
  -p 8501:8501 \
  --env-file .env \
  --restart unless-stopped \
  cynteka-dashboard

# 4. Проверить логи
docker logs cynteka-dashboard

# 5. Проверить статус
curl http://localhost:8501/_stcore/health
```

---

## Вариант 3: Reverse proxy через Nginx (для продакшн)

Если хотите использовать домен и HTTPS:

```bash
# 1. Установить Nginx
sudo apt update
sudo apt install nginx

# 2. Создать конфиг
sudo tee /etc/nginx/sites-available/cynteka << 'EOF'
server {
    listen 80;
    server_name cynteka.yourdomain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
EOF

# 3. Включить сайт
sudo ln -s /etc/nginx/sites-available/cynteka /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 4. (опционально) Добавить SSL через certbot
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d cynteka.yourdomain.com
```

---

## Текущий статус проекта

✅ Репозиторий создан: https://github.com/Artemtru/cynteka-dashboard  
✅ Код готов к работе  
✅ Зависимости установлены в `.venv`  
❌ Демон Streamlit не запущен (требуется root или Docker daemon)  
⏳ **Требуется API-токен Cynteka** для реальных данных

---

## Получение API-токена Cynteka

Обратитесь в техподдержку Cynteka:
- **Телефон**: 8-800-333-84-60
- **Email**: help@cynteka.ru

Попросите:
1. Endpoint API вашей инсталляции (обычно `https://api.cynteka.ru`)
2. API-токен с правами на чтение:
   - Проектов
   - Заявок
   - Счетов
   - Доставок
   - Сотрудников

После получения токена обновите `.env`:

```env
CYNTEKA_API_URL=https://api.cynteka.ru
CYNTEKA_API_TOKEN=ваш_реальный_токен_здесь
```

Затем перезапустите сервис:

```bash
sudo systemctl restart cynteka-dashboard
```

---

## Отладка

### Проверить логи

```bash
# Systemd
sudo journalctl -u cynteka-dashboard -f

# Docker
docker logs -f cynteka-dashboard

# Файл
tail -f /opt/data/cynteka-dashboard/streamlit.log
```

### Проверить процесс

```bash
ps aux | grep streamlit
netstat -tulpn | grep 8501
```

### Проверить порт занят

```bash
sudo lsof -i :8501
```

---

## Roadmap

После успешного деплоя и получения токена:

1. Реализовать реальные запросы к API в `cynteka_api.py`
2. Добавить экспорт отчётов в Excel
3. Добавить графики трендов
4. Интеграция с Telegram для алертов (как у Bybit бота)
5. Добавить уведомления о просрочках > 7 дней

---

Готово к развёртыванию! 🎉
