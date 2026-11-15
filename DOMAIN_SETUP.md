# Подключение домена syoma-dashboard.ru

Сейчас домен привязан к **хостингу REG.RU** и показывает заглушку
«Почти готово! Домен успешно привязан к хостингу». Обычный хостинг REG.RU
не умеет запускать Python/Streamlit, поэтому дашборд нужно открывать
с вашего сервера (VPS `13.140.145.240`), а домен — направить туда.

Схема: `браузер / Telegram → https://syoma-dashboard.ru → nginx (443) → Streamlit (127.0.0.1:8501)`

## 1. DNS в REG.RU (5 минут + до 24 ч на обновление)

1. Личный кабинет REG.RU → **Домены** → `syoma-dashboard.ru`.
2. Если домен привязан к услуге хостинга — отвяжите его от хостинга
   (или удалите сайт в панели хостинга), иначе REG.RU будет перезаписывать записи.
3. **DNS-серверы** — оставьте `ns1.reg.ru` / `ns2.reg.ru`.
4. **Управление зоной** → удалите старые A-записи для `@` и `www` и создайте:

| Тип | Имя | Значение |
|-----|-----|----------|
| A   | `@`   | `13.140.145.240` |
| A   | `www` | `13.140.145.240` |

Проверка (с любого компьютера): `nslookup syoma-dashboard.ru` → должен вернуть `13.140.145.240`.

## 2. Обновить код на сервере

```bash
ssh root@13.140.145.240
cd /opt/data/cynteka-dashboard
git pull
.venv/bin/pip install -r requirements.txt
sudo systemctl restart cynteka-dashboard
curl -s http://127.0.0.1:8501/_stcore/health   # должно вернуть: ok
```

## 3. Nginx + бесплатный SSL (Let's Encrypt)

Порты 80 и 443 должны быть открыты в файрволе / security group сервера.

```bash
sudo apt update && sudo apt install -y nginx certbot python3-certbot-nginx
sudo cp deploy/nginx/syoma-dashboard.ru.conf /etc/nginx/sites-available/syoma-dashboard.ru
sudo ln -sf /etc/nginx/sites-available/syoma-dashboard.ru /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# только после того, как DNS указывает на сервер (шаг 1):
sudo certbot --nginx -d syoma-dashboard.ru -d www.syoma-dashboard.ru --redirect
```

Проверка: `https://syoma-dashboard.ru` открывается с замком.

## 4. Telegram Mini App

Telegram открывает Mini App **только по https**, поэтому ссылка
`http://13.140.145.240:8501` не работала.

1. В `.env` на сервере: `WEBAPP_URL=https://syoma-dashboard.ru`
2. `sudo systemctl restart cynteka-telegram-bot`
3. @BotFather → `/mybots` → ваш бот → **Bot Settings → Menu Button** →
   URL `https://syoma-dashboard.ru`

## 5. (Рекомендуется) Закрыть прямой доступ к порту 8501

Когда домен заработал, Streamlit не должен быть доступен напрямую:

```bash
sudo sed -i 's/--server.address=0.0.0.0/--server.address=127.0.0.1/' /etc/systemd/system/cynteka-dashboard.service
sudo systemctl daemon-reload && sudo systemctl restart cynteka-dashboard
```

## Если не работает

| Симптом | Причина |
|---|---|
| Заглушка REG.RU | DNS ещё не обновился или домен всё ещё привязан к хостингу |
| `502 Bad Gateway` | Streamlit не запущен: `systemctl status cynteka-dashboard`, `journalctl -u cynteka-dashboard -n 50` |
| Вечное «Please wait…» | В nginx нет WebSocket-заголовков — используйте конфиг из `deploy/nginx/` |
| certbot: `Connection refused` / `Timeout` | Закрыт порт 80 или DNS ещё указывает не туда |
| «Доступ запрещён. Откройте дашборд через Telegram бота» | Это нормально при открытии в браузере — заходите через кнопку в боте |
