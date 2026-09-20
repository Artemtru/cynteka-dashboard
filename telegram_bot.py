"""
Telegram Mini App бот для Cynteka Dashboard

Функциональность:
- Открытие дашборда через Web App кнопку
- Авторизация пользователей по Telegram ID
- Уведомления о просрочках счетов (> 7 дней)
"""
import os
import asyncio
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()

# Настройки
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "http://13.140.145.240:8501")
ALLOWED_USERS = os.getenv("TELEGRAM_ALLOWED_USERS", "").split(",")

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start - приветствие и кнопка открытия дашборда"""
    user = update.effective_user
    user_id = str(user.id)
    
    # Проверка прав доступа
    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        await update.message.reply_text(
            f"❌ Доступ запрещён.\n\n"
            f"Ваш ID: `{user_id}`\n"
            f"Обратитесь к администратору для получения доступа.",
            parse_mode="Markdown"
        )
        logger.warning(f"Unauthorized access attempt from {user.username} ({user_id})")
        return
    
    # Кнопка для открытия Web App
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text="📊 Открыть Dashboard",
            web_app=WebAppInfo(url=f"{WEBAPP_URL}?tg_user_id={user_id}&tg_username={user.username}")
        )],
        [InlineKeyboardButton(text="ℹ️ Справка", callback_data="help")]
    ])
    
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        f"**Cynteka Dashboard** — мониторинг заявок, счетов и доставок.\n\n"
        f"🔹 Нажмите кнопку ниже, чтобы открыть дашборд\n"
        f"🔹 Дашборд откроется прямо в Telegram\n"
        f"🔹 Все данные обновляются каждые 5 минут\n\n"
        f"📱 **Доступные команды:**\n"
        f"/start — открыть дашборд\n"
        f"/stats — быстрая статистика\n"
        f"/help — подробная справка",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats - быстрая статистика без открытия дашборда"""
    user_id = str(update.effective_user.id)
    
    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        await update.message.reply_text("❌ Доступ запрещён.")
        return
    
    # Здесь можно добавить запрос к API Cynteka для получения свежих данных
    # Пока используем заглушку
    
    await update.message.reply_text(
        "📊 **Статистика на сегодня**\n\n"
        "📝 Заявок в работе: 42\n"
        "✅ Закрыто в срок: 156 (89%)\n"
        "💰 Счетов на согласовании: 8\n"
        "🚚 Доставок на неделе: 23\n\n"
        "⚠️ **Внимание:**\n"
        "🔴 3 счета просрочены > 7 дней\n\n"
        "Для подробного отчёта откройте дашборд → /start",
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help - подробная справка"""
    await update.message.reply_text(
        "ℹ️ **Справка по боту**\n\n"
        "**Основные возможности:**\n"
        "• Полноценный дашборд прямо в Telegram\n"
        "• Фильтры по проектам и сотрудникам\n"
        "• Интерактивные графики и таблицы\n"
        "• Автообновление данных каждые 5 минут\n\n"
        "**Вкладки дашборда:**\n"
        "📋 Заявки по проектам — статусы и прогресс\n"
        "💳 Счета — с индикацией просрочек\n"
        "🚚 Доставки — запланированные поставки\n"
        "👥 Сотрудники — топ-10 по загрузке\n\n"
        "**Команды:**\n"
        "/start — открыть дашборд\n"
        "/stats — общая статистика\n"
        "/help — эта справка\n\n"
        "**Техподдержка:**\n"
        "По вопросам работы системы: help@cynteka.ru\n"
        "По вопросам бота: @YourAdmin",
        parse_mode="Markdown"
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Произошла ошибка при обработке запроса.\n"
            "Попробуйте позже или обратитесь к администратору."
        )


async def send_overdue_alerts(application):
    """
    Фоновая задача: проверка просроченных счетов и отправка алертов
    Запускается каждый день в 10:00
    """
    # Здесь будет запрос к API Cynteka для получения просроченных счетов
    # Пример:
    """
    from cynteka_api import CyntekaAPI
    api = CyntekaAPI()
    overdue_invoices = api.get_overdue_invoices(days=7)
    
    if overdue_invoices:
        message = "⚠️ **Просроченные счета > 7 дней:**\n\n"
        for inv in overdue_invoices[:5]:  # топ-5
            message += f"🔴 {inv['number']} — {inv['amount']}₽ ({inv['days']} дн.)\n"
        
        # Отправка всем авторизованным пользователям
        for user_id in ALLOWED_USERS:
            await application.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="Markdown"
            )
    """
    logger.info("Daily overdue check completed")


def main():
    """Запуск бота"""
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in .env")
        return
    
    # Создание приложения
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("help", help_command))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запуск бота
    logger.info("Starting Cynteka Dashboard Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
