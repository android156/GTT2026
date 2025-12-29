from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='admin')
    is_active = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Page(db.Model):
    __tablename__ = 'pages'
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    url_path = db.Column(db.String(200), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content_html = db.Column(db.Text, default='')
    seo_title = db.Column(db.String(200), default='')
    seo_description = db.Column(db.String(300), default='')
    h1 = db.Column(db.String(200), default='')
    seo_text_html = db.Column(db.Text, default='')
    hero_image = db.Column(db.String(300), default='')
    hero_title = db.Column(db.String(200), default='')
    hero_subtitle = db.Column(db.String(300), default='')
    is_published = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    is_external = db.Column(db.Boolean, default=False)
    nofollow = db.Column(db.Boolean, default=False)
    target_blank = db.Column(db.Boolean, default=False)
    hero_image = db.Column(db.String(300), default='')
    hero_title = db.Column(db.String(200), default='')
    hero_subtitle = db.Column(db.String(300), default='')


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description_html = db.Column(db.Text, default='')
    image_path = db.Column(db.String(300), default='')
    seo_title = db.Column(db.String(200), default='')
    seo_description = db.Column(db.String(300), default='')
    h1 = db.Column(db.String(200), default='')
    seo_text_html = db.Column(db.Text, default='')
    hero_image = db.Column(db.String(300), default='')
    hero_title = db.Column(db.String(200), default='')
    hero_subtitle = db.Column(db.String(300), default='')
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    product_lines = db.relationship('ProductLine', backref='category', lazy='dynamic', cascade='all, delete-orphan')


class ProductLine(db.Model):
    __tablename__ = 'product_lines'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(100), nullable=False)
    description_html = db.Column(db.Text, default='')
    image_path = db.Column(db.String(300), default='')
    seo_title = db.Column(db.String(200), default='')
    seo_description = db.Column(db.String(300), default='')
    h1 = db.Column(db.String(200), default='')
    seo_text_html = db.Column(db.Text, default='')
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    size_items = db.relationship('SizeItem', backref='product_line', lazy='dynamic', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.UniqueConstraint('category_id', 'slug', name='uq_productline_category_slug'),
    )


class SizeItem(db.Model):
    __tablename__ = 'size_items'
    id = db.Column(db.Integer, primary_key=True)
    product_line_id = db.Column(db.Integer, db.ForeignKey('product_lines.id'), nullable=False)
    size_text = db.Column(db.String(100), nullable=False)
    size_slug = db.Column(db.String(100), nullable=False)
    full_name = db.Column(db.String(300), default='')
    sku = db.Column(db.String(100), default='')
    price = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(10), default='RUB')
    unit = db.Column(db.String(20), default='шт')
    in_stock = db.Column(db.Boolean, default=True)
    image_path = db.Column(db.String(300), default='')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('product_line_id', 'size_slug', name='uq_sizeitem_productline_slug'),
    )


class News(db.Model):
    __tablename__ = 'news'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    content_html = db.Column(db.Text, default='')
    seo_title = db.Column(db.String(200), default='')
    seo_description = db.Column(db.String(300), default='')
    h1 = db.Column(db.String(200), default='')
    seo_text_html = db.Column(db.Text, default='')
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DocumentFile(db.Model):
    __tablename__ = 'document_files'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(300), nullable=False)
    doc_type = db.Column(db.String(50), default='other')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Lead(db.Model):
    __tablename__ = 'leads'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), default='')
    phone = db.Column(db.String(50), default='')
    email = db.Column(db.String(200), default='')
    message = db.Column(db.Text, default='')
    source = db.Column(db.String(50), default='site')
    status = db.Column(db.String(50), default='new')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    content_html = db.Column(db.Text, default='')
    image_path = db.Column(db.String(300), default='')
    seo_title = db.Column(db.String(200), default='')
    seo_description = db.Column(db.String(300), default='')
    h1 = db.Column(db.String(200), default='')
    seo_text_html = db.Column(db.Text, default='')
    hero_image = db.Column(db.String(300), default='')
    hero_title = db.Column(db.String(200), default='')
    hero_subtitle = db.Column(db.String(300), default='')
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RedirectRule(db.Model):
    __tablename__ = 'redirect_rules'
    id = db.Column(db.Integer, primary_key=True)
    from_path = db.Column(db.String(500), nullable=False)
    to_path = db.Column(db.String(500), nullable=False)
    code = db.Column(db.Integer, default=301)
    is_active = db.Column(db.Boolean, default=True)
    comment = db.Column(db.String(300), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Setting(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, default='')
    description = db.Column(db.String(300), default='')


class SiteSection(db.Model):
    __tablename__ = 'site_sections'
    id = db.Column(db.Integer, primary_key=True)
    section_key = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(200), default='')
    content_html = db.Column(db.Text, default='')
    seo_title = db.Column(db.String(200), default='')
    seo_description = db.Column(db.String(300), default='')
    h1 = db.Column(db.String(200), default='')
    seo_text_html = db.Column(db.Text, default='')
    hero_image = db.Column(db.String(300), default='')
    hero_title = db.Column(db.String(200), default='')
    hero_subtitle = db.Column(db.String(300), default='')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
