import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.environ.get('SESSION_SECRET') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///glavtrubtorg.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
    TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
    TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
    
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg', 'gif'}
    
    SITE_NAME = 'ГлавТрубТорг'
    SITE_URL = os.environ.get('SITE_URL', 'https://glavtrubtorg.ru')

RESERVED_SLUGS = [
    'about', 'catalog', 'services', 'price', 'documentation', 
    'contacts', 'news', 'static', 'admin', 'login', 'logout',
    'sitemap.xml', 'robots.txt', 'api'
]
