import requests
import logging
from models import Setting

logger = logging.getLogger(__name__)


def get_telegram_settings():
    """Get Telegram bot token and chat ID from database settings."""
    token = None
    chat_id = None
    
    token_setting = Setting.query.filter_by(key='TELEGRAM_TOKEN').first()
    if token_setting:
        token = token_setting.value
    
    chat_id_setting = Setting.query.filter_by(key='TELEGRAM_CHAT_ID').first()
    if chat_id_setting:
        chat_id = chat_id_setting.value
    
    return token, chat_id


def send_lead_to_telegram(name, phone, email, message, page_url='', utm_params=None):
    """Send lead notification to Telegram group chat."""
    token, chat_id = get_telegram_settings()
    
    if not token or not chat_id:
        logger.warning("Telegram credentials not configured")
        return False
    
    if utm_params is None:
        utm_params = {}
    
    text_parts = ["🔥 *Новая заявка*\n"]
    
    if name:
        text_parts.append(f"👤 *Имя:* {escape_markdown(name)}")
    if phone:
        text_parts.append(f"📞 *Телефон:* {escape_markdown(phone)}")
    if email:
        text_parts.append(f"📧 *Email:* {escape_markdown(email)}")
    if message:
        text_parts.append(f"💬 *Сообщение:* {escape_markdown(message)}")
    if page_url:
        text_parts.append(f"📄 *Страница:* {escape_markdown(page_url)}")
    
    utm_parts = []
    for key, value in (utm_params or {}).items():
        if value:
            utm_parts.append(f"{key.replace('utm_', '')}={escape_markdown(value)}")
    
    if utm_parts:
        text_parts.append(f"🔗 *UTM:* {', '.join(utm_parts)}")
    
    text = "\n".join(text_parts)
    
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"Lead sent to Telegram chat {chat_id}")
            return True
        else:
            logger.error(f"Telegram API error: {response.status_code} - {response.text}")
            return False
    
    except requests.RequestException as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False


def escape_markdown(text):
    """Escape special characters for Telegram Markdown."""
    if not text:
        return ""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = str(text).replace(char, '\\' + char)
    return text
