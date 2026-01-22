import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger(__name__)

SMTP_HOST = 'smtp.yandex.ru'
SMTP_PORT = 465
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
DEFAULT_RECIPIENT = os.environ.get('LEAD_EMAIL', 'sale@glavtrubtorg.ru')


def send_lead_email(name, phone, email, message, page_url='', utm_params=None):
    """Send lead notification email via Yandex SMTP SSL."""
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.error("SMTP credentials not configured")
        return False
    
    if utm_params is None:
        utm_params = {}
    
    now = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    
    contact_info = phone or email or 'не указан'
    subject = f"Заявка с сайта: {name} {contact_info}"
    
    body_parts = [
        f"Имя: {name}",
        f"Телефон: {phone or 'не указан'}",
        f"Email: {email or 'не указан'}",
        f"Сообщение: {message or 'не указано'}",
        f"Страница: {page_url or 'не указана'}",
        f"Дата/время: {now}",
    ]
    
    if utm_params:
        body_parts.append("")
        body_parts.append("UTM-метки:")
        for key, value in utm_params.items():
            if value:
                body_parts.append(f"  {key}: {value}")
    
    body = "\n".join(body_parts)
    
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = DEFAULT_RECIPIENT
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Lead email sent successfully to {DEFAULT_RECIPIENT}")
        return True
    
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP authentication failed: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False
