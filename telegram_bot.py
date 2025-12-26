import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

flask_app = None
db = None
Lead = None


def init_flask_app():
    global flask_app, db, Lead
    if flask_app is None:
        from app import create_app
        from extensions import db as _db
        from models import Lead as _Lead
        flask_app = create_app()
        db = _db
        Lead = _Lead
        logger.info("Flask app initialized for Telegram bot")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать в ГлавТрубТорг!\n\n"
        "Вы можете оставить заявку, написав сообщение.\n"
        "Наш менеджер свяжется с вами в ближайшее время.\n\n"
        "Также посетите наш сайт: https://glavtrubtorg.ru"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message_text = update.message.text
    
    from services.rag_service import ask
    answer = ask(message_text)
    
    await update.message.reply_text(
        f"Спасибо за обращение!\n\n{answer}\n\n"
        "Ваша заявка принята. Мы свяжемся с вами в ближайшее время."
    )
    
    if TELEGRAM_CHAT_ID:
        try:
            notification = (
                f"Новая заявка из Telegram!\n\n"
                f"От: {user.full_name} (@{user.username or 'нет'})\n"
                f"Сообщение: {message_text}"
            )
            await context.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=notification)
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    try:
        with flask_app.app_context():
            lead = Lead(
                name=user.full_name or '',
                phone='',
                email='',
                message=message_text,
                source='telegram',
                status='new'
            )
            db.session.add(lead)
            db.session.commit()
            logger.info(f"Lead saved from Telegram: {user.full_name}")
    except Exception as e:
        logger.error(f"Failed to save lead: {e}")


def main():
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN not set. Please set the environment variable.")
        return
    
    init_flask_app()
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Starting Telegram bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
