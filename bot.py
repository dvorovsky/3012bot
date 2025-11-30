import logging
import asyncio
from datetime import datetime, time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота (замените на ваш токен)
BOT_TOKEN = "8536999712:AAFhh5Vvz6PSZ8cipwd8H_0TL3vYgG4_BPU"

# Словарь для хранения chat_id пользователей, которые подписались на уведомления
subscribed_users = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    welcome_text = """
Привет! 👋 Я бот, который считает дни до 30 декабря.

Доступные команды:
/days - Показать сколько дней осталось до 30 декабря
/subscribe - Подписаться на ежедневные уведомления
/unsubscribe - Отписаться от уведомлений
/start - Начало работы
/help - Помощь
    """
    await update.message.reply_text(welcome_text)

async def days_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /days"""
    days_left = calculate_days_until_december_30()
    message = format_days_message(days_left)
    await update.message.reply_text(message)

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /subscribe"""
    chat_id = update.effective_chat.id
    
    if chat_id in subscribed_users:
        await update.message.reply_text("✅ Вы уже подписаны на ежедневные уведомления!")
    else:
        subscribed_users.add(chat_id)
        await update.message.reply_text(
            "✅ Вы успешно подписались на ежедневные уведомления!\n"
            "Я буду присылать вам сообщение каждый день в 10:00 утра.\n"
            "Чтобы отписаться, используйте /unsubscribe"
        )

async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /unsubscribe"""
    chat_id = update.effective_chat.id
    
    if chat_id in subscribed_users:
        subscribed_users.remove(chat_id)
        await update.message.reply_text("❌ Вы отписались от ежедневных уведомлений.")
    else:
        await update.message.reply_text("ℹ️ Вы не были подписаны на уведомления.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    help_text = """
🤖 Помощь по боту:

/days - Узнать сколько дней осталось до 30 декабря
/subscribe - Подписаться на ежедневные уведомления в 10:00
/unsubscribe - Отписаться от уведомлений
/start - Начать работу с ботом
/help - Показать эту справку

Бот автоматически считает дни до ближайшего 30 декабря!
    """
    await update.message.reply_text(help_text)

def calculate_days_until_december_30() -> int:
    """Рассчитывает количество дней до 30 декабря"""
    today = datetime.now().date()
    current_year = today.year
    
    # Создаем дату 30 декабря текущего года
    target_date = datetime(current_year, 12, 30).date()
    
    # Если 30 декабря уже прошло в этом году, берем следующий год
    if today > target_date:
        target_date = datetime(current_year + 1, 12, 30).date()
    
    # Вычисляем разницу в днях
    days_difference = (target_date - today).days
    return days_difference

def format_days_message(days_left: int) -> str:
    """Форматирует сообщение о количестве оставшихся дней"""
    if days_left == 0:
        return "🎉🎉 Ура! Сегодня 30 декабря! 🎉🎉"
    elif days_left == 1:
        return "🚨🚨🚨🚨🚨 Завтра 30 декабря! Остался всего 1 день! 🚨🚨🚨🚨🚨"
    elif days_left < 0:
        return f"🙁 30 декабря уже прошло! Следующее 30 декабря через {365 + days_left} дней 📅"
    else:
        return f"🚨🚨🚨Oсталось {days_left} дней 🚨🚨🚨"

async def send_daily_notifications(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет ежедневные уведомления всем подписанным пользователям"""
    if not subscribed_users:
        return
    
    days_left = calculate_days_until_december_30()
    message = format_days_message(days_left)
    
    for chat_id in list(subscribed_users):
        try:
            await context.bot.send_message(chat_id=chat_id, text=message)
            logger.info(f"Уведомление отправлено пользователю {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки пользователю {chat_id}: {e}")
            # Если пользователь заблокировал бота, удаляем его из списка
            subscribed_users.discard(chat_id)

async def check_time_and_notify(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Проверяет время и отправляет уведомления если настало 10:00"""
    now = datetime.now().time()
    
    # Проверяем, сейчас ли 10:00 (можно изменить на нужное время)
    if now.hour == 10 and now.minute == 0:
        await send_daily_notifications(context)

async def daily_scheduler(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Планировщик для ежедневной проверки"""
    while True:
        await check_time_and_notify(context)
        # Проверяем каждую минуту
        await asyncio.sleep(60)

def main() -> None:
    """Основная функция запуска бота"""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("days", days_command))
    application.add_handler(CommandHandler("subscribe", subscribe_command))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Запускаем планировщик при старте бота
    application.job_queue.run_once(
        lambda context: asyncio.create_task(daily_scheduler(context)),
        when=1
    )
    
    # Запускаем бота
    print("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()