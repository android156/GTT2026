import os
import logging
from datetime import datetime
from flask import Flask, render_template
from config import Config
from extensions import db, migrate, login_manager, csrf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    
    @app.after_request
    def add_header(response):
        from flask import request
        if request.path.startswith('/wm/') or request.path.startswith('/static/'):
            return response
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    from blueprints.public import public_bp
     
    from blueprints.admin import admin_bp
    from blueprints.public_services import public_services_bp
    from blueprints.redirects import check_redirects
    
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(public_services_bp)
    
    check_redirects(app)
    
    from cli.admin import admin_cli
    app.cli.add_command(admin_cli)
    
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow}
    
    @app.template_global()
    def watermark_url(image_type, image_id):
        """Generate URL for watermarked gallery image."""
        return f'/wm/{image_type}/{image_id}/'
    
    @app.errorhandler(404)
    def not_found(e):
        return render_template('public/404.html'), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return render_template('public/500.html'), 500
    
    with app.app_context():
        db.create_all()
        init_default_data()
    
    return app


def init_default_data():
    from models import Page, MenuItem, Setting
    
    default_pages = [
        {'slug': 'about', 'url_path': '/about/', 'title': 'О компании', 'content_html': '<p>Информация о компании ГлавТрубТорг.</p>'},
        {'slug': 'services', 'url_path': '/services/', 'title': 'Услуги', 'content_html': '<p>Наши услуги.</p>'},
        {'slug': 'price', 'url_path': '/price/', 'title': 'Цены', 'content_html': '<p>Прайс-лист.</p>'},
        {'slug': 'documentation', 'url_path': '/documentation/', 'title': 'Документация', 'content_html': '<p>Документы и сертификаты.</p>'},
        {'slug': 'contacts', 'url_path': '/contacts/', 'title': 'Контакты', 'content_html': '<p>Контактная информация.</p>'},
    ]
    
    for page_data in default_pages:
        if not Page.query.filter_by(slug=page_data['slug']).first():
            page = Page(**page_data, is_published=True)
            db.session.add(page)
    
    default_menu = [
        {'title': 'О компании', 'url': '/about/', 'sort_order': 1},
        {'title': 'Новости', 'url': '/news/', 'sort_order': 2},
        {'title': 'Продукция', 'url': '/catalog/', 'sort_order': 3},
        {'title': 'Услуги', 'url': '/services/', 'sort_order': 4},
        {'title': 'Цены', 'url': '/price/', 'sort_order': 5},
        {'title': 'Документация', 'url': '/documentation/', 'sort_order': 6},
        {'title': 'Контакты', 'url': '/contacts/', 'sort_order': 7},
    ]
    
    if not MenuItem.query.first():
        for item_data in default_menu:
            item = MenuItem(**item_data, is_active=True)
            db.session.add(item)
    
    default_settings = [
        {'key': 'TELEGRAM_TOKEN', 'value': '', 'description': 'Токен Telegram бота'},
        {'key': 'TELEGRAM_CHAT_ID', 'value': '', 'description': 'ID чата для уведомлений'},
        {'key': 'PHONE', 'value': '', 'description': 'Контактный телефон'},
        {'key': 'EMAIL', 'value': '', 'description': 'Контактный email'},
        {'key': 'ADDRESS', 'value': '', 'description': 'Адрес'},
    ]
    
    for setting_data in default_settings:
        if not Setting.query.filter_by(key=setting_data['key']).first():
            setting = Setting(**setting_data)
            db.session.add(setting)
    
    db.session.commit()


app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
