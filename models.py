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
    seo_description = db.Column(db.String(1000), default='')
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
    seo_description = db.Column(db.String(1000), default='')
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
    seo_description = db.Column(db.String(1000), default='')
    h1 = db.Column(db.String(200), default='')
    seo_text_html = db.Column(db.Text, default='')
    hero_image = db.Column(db.String(300), default='')
    hero_title = db.Column(db.String(200), default='')
    hero_subtitle = db.Column(db.String(300), default='')
    gallery_interval = db.Column(db.Integer, default=5)
    discount_percent = db.Column(db.Float, default=0.0)
    hide_price = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    size_items = db.relationship('SizeItem', backref='product_line', lazy='dynamic', cascade='all, delete-orphan')
    images = db.relationship('ProductLineImage', backref='product_line', lazy='dynamic', cascade='all, delete-orphan')
    accessory_blocks = db.relationship('AccessoryBlock', backref='product_line', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_main_image(self):
        images_list = self.images.order_by('sort_order').all()
        for img in images_list:
            if img.is_main:
                return img.image_path
        if images_list:
            return images_list[0].image_path
        return self.image_path if self.image_path else ''
    
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
    discount_percent = db.Column(db.Float, nullable=True)
    hide_price = db.Column(db.Boolean, nullable=True)
    
    # Новые параметры
    pipe_dxs = db.Column(db.String(100), default='')  # Напорная труба DxS, мм
    pressure = db.Column(db.String(50), default='')   # Давление
    mass_per_m = db.Column(db.String(50), default='') # Масса 1м, кг
    min_bend_radius = db.Column(db.String(50), default='') # Мин. радиус изгиба, м
    max_len_coil = db.Column(db.String(50), default='')    # Макс. длина в бухте, м
    max_len_drum = db.Column(db.String(50), default='')    # Макс. длина на барабане, м
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_effective_discount(self):
        """Возвращает эффективную скидку (из типоразмера или линейки)"""
        if self.discount_percent is not None:
            return self.discount_percent
        return self.product_line.discount_percent if self.product_line else 0.0
    
    def get_effective_hide_price(self):
        """Возвращает эффективный флаг скрытия цены (из типоразмера или линейки)"""
        if self.hide_price is not None:
            return self.hide_price
        return self.product_line.hide_price if self.product_line else False
    
    def get_display_price(self):
        """Возвращает цену с учётом скидки, округлённую до 2 знаков"""
        if self.price is None or self.price == 0:
            return 0.0
        discount = self.get_effective_discount()
        if discount > 0:
            discounted = self.price * (1 - discount / 100)
            return round(discounted, 2)
        return round(self.price, 2)
    
    __table_args__ = (
        db.UniqueConstraint('product_line_id', 'size_slug', name='uq_sizeitem_productline_slug'),
    )


class News(db.Model):
    __tablename__ = 'news'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=True)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    content_html = db.Column(db.Text, default='')
    seo_title = db.Column(db.String(200), default='')
    seo_description = db.Column(db.String(1000), default='')
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
    seo_description = db.Column(db.String(1000), default='')
    h1 = db.Column(db.String(200), default='')
    seo_text_html = db.Column(db.Text, default='')
    hero_image = db.Column(db.String(300), default='')
    hero_title = db.Column(db.String(200), default='')
    hero_subtitle = db.Column(db.String(300), default='')
    gallery_interval = db.Column(db.Integer, default=5)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    images = db.relationship('ServiceImage', backref='service', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_main_image(self):
        main = ServiceImage.query.filter_by(service_id=self.id, is_main=True).first()
        if main:
            return main.image_path
        first = ServiceImage.query.filter_by(service_id=self.id).order_by(ServiceImage.sort_order).first()
        if first:
            return first.image_path
        return self.image_path if self.image_path else ''


class ServiceImage(db.Model):
    __tablename__ = 'service_images'
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    image_path = db.Column(db.String(300), nullable=False)
    alt_text = db.Column(db.String(200), default='')
    title_text = db.Column(db.String(200), default='')
    caption = db.Column(db.String(500), default='')
    is_main = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    rotation = db.Column(db.Integer, default=0)  # 0, 90, 180, 270 degrees
    no_watermark = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class HomeGalleryImage(db.Model):
    __tablename__ = 'home_gallery_images'
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(300), nullable=False)
    alt_text = db.Column(db.String(200), default='')
    title_text = db.Column(db.String(200), default='')
    caption = db.Column(db.String(500), default='')
    sort_order = db.Column(db.Integer, default=0)
    rotation = db.Column(db.Integer, default=0)
    no_watermark = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


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
    seo_description = db.Column(db.String(1000), default='')
    h1 = db.Column(db.String(200), default='')
    seo_text_html = db.Column(db.Text, default='')
    hero_image = db.Column(db.String(300), default='')
    hero_title = db.Column(db.String(200), default='')
    hero_subtitle = db.Column(db.String(300), default='')
    gallery_interval = db.Column(db.Integer, default=5)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProductLineImage(db.Model):
    __tablename__ = 'product_line_images'
    id = db.Column(db.Integer, primary_key=True)
    product_line_id = db.Column(db.Integer, db.ForeignKey('product_lines.id'), nullable=False)
    image_path = db.Column(db.String(300), nullable=False)
    alt_text = db.Column(db.String(200), default='')
    title_text = db.Column(db.String(200), default='')
    caption = db.Column(db.String(500), default='')
    is_main = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    rotation = db.Column(db.Integer, default=0)
    no_watermark = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AccessoryBlock(db.Model):
    __tablename__ = 'accessory_blocks'
    id = db.Column(db.Integer, primary_key=True)
    product_line_id = db.Column(db.Integer, db.ForeignKey('product_lines.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description_html = db.Column(db.Text, default='')
    image_path = db.Column(db.String(300), default='')
    table_html = db.Column(db.Text, default='')
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
