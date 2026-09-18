# 🎯 Краткая инструкция по запуску

Дашборд готов! Осталось запустить на VPS.

## Быстрый старт (2 команды)

Выполните **на хосте VPS** (не в Docker):

```bash
# Создать и запустить systemd сервис
sudo cp /opt/data/cynteka-dashboard/cynteka-dashboard.service /etc/systemd/system/ && \
sudo systemctl daemon-reload && \
sudo systemctl enable --now cynteka-dashboard && \
sudo systemctl status cynteka-dashboard

# Проверить работу
curl http://localhost:8501/_stcore/health
```

Дашборд доступен: **http://13.140.145.240:8501**

---

## Что дальше?

1. **Получить API-токен Cynteka**
   - Позвонить: 8-800-333-84-60
   - Email: help@cynteka.ru
   - Запросить endpoint + токен для чтения заявок/счетов/доставок

2. **Обновить `.env`**
   ```bash
   nano /opt/data/cynteka-dashboard/.env
   # Вставить реальный токен
   sudo systemctl restart cynteka-dashboard
   ```

3. **Реализовать API-интеграцию**
   - Отредактировать `cynteka_api.py`
   - Заменить заглушки на реальные запросы
   - Документация API обычно в личном кабинете Cynteka

---

## Управление сервисом

```bash
# Статус
sudo systemctl status cynteka-dashboard

# Логи
sudo journalctl -u cynteka-dashboard -f

# Перезапуск
sudo systemctl restart cynteka-dashboard

# Остановка
sudo systemctl stop cynteka-dashboard
```

---

## Полная документация

- [DEPLOY.md](DEPLOY.md) — 3 варианта установки
- [README.md](README.md) — функциональность, разработка
- GitHub: https://github.com/Artemtru/cynteka-dashboard

---

**Время разработки**: 2 часа  
**Статус**: Готов к деплою, требуется API-токен Cynteka
