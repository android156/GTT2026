from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify, Response, make_response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db, login_manager
from models import User, Page, MenuItem, Category, ProductLine, SizeItem, News, DocumentFile, Lead, RedirectRule, Setting, Service, SiteSection, ServiceImage, HomeGalleryImage, ProductLineImage, AccessoryBlock, AccessoryImage
from services.importers import import_categories_csv, import_product_lines_csv, import_size_items_csv, import_news_csv
from services.slug import generate_slug, is_reserved_slug, validate_slug
from services.image_uploader import save_uploaded_image, delete_image
from config import Config
import os
import bleach

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                'ul', 'ol', 'li', 'a', 'img', 'table', 'tr', 'td', 'th', 'thead', 'tbody',
                'blockquote', 'pre', 'code', 'hr', 'div', 'span']
ALLOWED_ATTRS = {'a': ['href', 'title', 'target', 'rel'], 'img': ['src', 'alt', 'title', 'width', 'height'],
                 '*': ['class', 'id', 'style']}


def sanitize_html(html):
    if not html:
        return ''
    return bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@admin_bp.route('/login/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password) and user.is_active:
            login_user(user)
            flash('Вы успешно вошли в систему', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Неверный логин или пароль', 'danger')
    
    return render_template('admin/login.html')


@admin_bp.route('/logout/')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('admin.login'))


@admin_bp.route('/csv-template/<template_type>/')
@login_required
def csv_template(template_type):
    templates = {
        'categories': {
            'filename': 'categories_template.csv',
            'headers': 'name;slug;sort_order;is_active;seo_title;seo_description;h1;seo_text_html',
            'example': 'Полиэтиленовые трубы;polietilenovye-truby;1;1;Трубы — купить;;Полиэтиленовые трубы;'
        },
        'product_lines': {
            'filename': 'product_lines_template.csv',
            'headers': 'category_slug;name;slug;sort_order;is_active;seo_title;seo_description;h1;seo_text_html',
            'example': 'polietilenovye-truby;ПЭ 100 SDR 11;pe-100-sdr-11;1;1;;;ПЭ 100 SDR 11;'
        },
        'size_items': {
            'filename': 'size_items_template.csv',
            'headers': 'category_slug;product_slug;size_text;sku;price;unit;in_stock;pipe_dxs;pressure;mass_per_m;min_bend_radius;max_len_coil;max_len_drum',
            'example': 'polietilenovye-truby;pe-100-sdr-11;32x3.0;PE100-32-3;150.00;м;1;32x3.0;1.0 МПа;0.29;0.5;200;500'
        },
        'news': {
            'filename': 'news_template.csv',
            'headers': 'date;title;slug;content;seo_title;seo_description;h1;is_published',
            'example': '15.01.2025;Новость о расширении ассортимента;novost-o-rasshirenii;Компания расширила ассортимент продукции;;;;1'
        }
    }
    
    if template_type not in templates:
        flash('Неизвестный тип шаблона', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    t = templates[template_type]
    content = t['headers'] + '\n' + t['example'] + '\n'
    
    return Response(
        content,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={t["filename"]}'}
    )


def escape_csv_field(value):
    if value is None:
        return ''
    s = str(value)
    if ';' in s or '"' in s or '\n' in s:
        return '"' + s.replace('"', '""') + '"'
    return s


@admin_bp.route('/csv-export/categories/')
@login_required
def csv_export_categories():
    search = request.args.get('search', '', type=str).strip().lower()
    query = Category.query
    if search:
        query = query.filter(Category.name.ilike(f'%{search}%'))
    categories = query.order_by(Category.sort_order).all()
    lines = ['name;slug;sort_order;is_active;seo_title;seo_description;h1;seo_text_html']
    for c in categories:
        row = ';'.join([
            escape_csv_field(c.name),
            escape_csv_field(c.slug),
            str(c.sort_order or 0),
            '1' if c.is_active else '0',
            escape_csv_field(c.seo_title),
            escape_csv_field(c.seo_description),
            escape_csv_field(c.h1),
            escape_csv_field(c.seo_text_html)
        ])
        lines.append(row)
    content = '\n'.join(lines) + '\n'
    return Response(
        content,
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename=categories_export.csv'}
    )


@admin_bp.route('/csv-export/product-lines/')
@login_required
def csv_export_product_lines():
    category_id = request.args.get('category_id', '', type=str)
    search = request.args.get('search', '', type=str).strip().lower()
    
    query = ProductLine.query.join(Category)
    
    if category_id:
        query = query.filter(ProductLine.category_id == int(category_id))
    if search:
        query = query.filter(
            db.or_(
                Category.name.ilike(f'%{search}%'),
                ProductLine.name.ilike(f'%{search}%')
            )
        )
        
    product_lines = query.order_by(Category.sort_order, ProductLine.sort_order).all()
    lines = ['category_slug;name;slug;sort_order;is_active;seo_title;seo_description;h1;seo_text_html']
    for pl in product_lines:
        row = ';'.join([
            escape_csv_field(pl.category.slug),
            escape_csv_field(pl.name),
            escape_csv_field(pl.slug),
            str(pl.sort_order or 0),
            '1' if pl.is_active else '0',
            escape_csv_field(pl.seo_title),
            escape_csv_field(pl.seo_description),
            escape_csv_field(pl.h1),
            escape_csv_field(pl.seo_text_html)
        ])
        lines.append(row)
    content = '\n'.join(lines) + '\n'
    return Response(
        content,
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename=product_lines_export.csv'}
    )


@admin_bp.route('/csv-export/size-items/')
@login_required
def csv_export_size_items():
    category_id = request.args.get('category_id', '', type=str)
    product_line_id = request.args.get('product_line_id', '', type=str)
    search = request.args.get('search', '', type=str).strip().lower()
    
    query = SizeItem.query.join(ProductLine).join(Category)
    
    if category_id:
        query = query.filter(ProductLine.category_id == int(category_id))
    if product_line_id:
        query = query.filter(SizeItem.product_line_id == int(product_line_id))
    if search:
        query = query.filter(
            db.or_(
                Category.name.ilike(f'%{search}%'),
                ProductLine.name.ilike(f'%{search}%'),
                SizeItem.size_text.ilike(f'%{search}%')
            )
        )
        
    size_items = query.order_by(
        Category.sort_order, ProductLine.sort_order, SizeItem.size_text
    ).all()
    lines = ['category_slug;product_slug;size_text;sku;price;unit;in_stock;pipe_dxs;pressure;mass_per_m;min_bend_radius;max_len_coil;max_len_drum']
    for si in size_items:
        row = ';'.join([
            escape_csv_field(si.product_line.category.slug),
            escape_csv_field(si.product_line.slug),
            escape_csv_field(si.size_text),
            escape_csv_field(si.sku),
            str(si.price or 0),
            escape_csv_field(si.unit),
            '1' if si.in_stock else '0',
            escape_csv_field(si.pipe_dxs),
            escape_csv_field(si.pressure),
            escape_csv_field(si.mass_per_m),
            escape_csv_field(si.min_bend_radius),
            escape_csv_field(si.max_len_coil),
            escape_csv_field(si.max_len_drum)
        ])
        lines.append(row)
    content = '\n'.join(lines) + '\n'
    return Response(
        content,
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename=size_items_export.csv'}
    )


@admin_bp.route('/csv-export/news/')
@login_required
def csv_export_news():
    search = request.args.get('search', '', type=str).strip().lower()
    query = News.query
    if search:
        query = query.filter(News.title.ilike(f'%{search}%'))
        
    news_list = query.order_by(News.date.desc()).all()
    lines = ['date;title;slug;content;seo_title;seo_description;h1;is_published']
    for n in news_list:
        date_str = n.date.strftime('%d.%m.%Y') if n.date else ''
        row = ';'.join([
            date_str,
            escape_csv_field(n.title),
            escape_csv_field(n.slug),
            escape_csv_field(n.content_html),
            escape_csv_field(n.seo_title),
            escape_csv_field(n.seo_description),
            escape_csv_field(n.h1),
            '1' if n.is_published else '0'
        ])
        lines.append(row)
    content = '\n'.join(lines) + '\n'
    return Response(
        content,
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename=news_export.csv'}
    )


@admin_bp.route('/')
@login_required
def dashboard():
    stats = {
        'pages': Page.query.count(),
        'categories': Category.query.count(),
        'product_lines': ProductLine.query.count(),
        'size_items': SizeItem.query.count(),
        'news': News.query.count(),
        'leads': Lead.query.filter_by(status='new').count(),
        'redirects': RedirectRule.query.filter_by(is_active=True).count(),
        'services': Service.query.count()
    }
    recent_leads = Lead.query.order_by(Lead.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html', stats=stats, recent_leads=recent_leads)


SECTION_TITLES = {
    'index': 'Главная страница',
    'news': 'Раздел новостей',
    'catalog': 'Каталог',
    'services': 'Раздел услуг'
}

@admin_bp.route('/sections/<section_key>/', methods=['GET', 'POST'])
@login_required
def section_edit(section_key):
    section = SiteSection.query.filter_by(section_key=section_key).first()
    if not section:
        section = SiteSection(section_key=section_key, title=SECTION_TITLES.get(section_key, section_key))
        db.session.add(section)
        db.session.commit()
    
    if request.method == 'POST':
        if 'hero_image_file' in request.files:
            file = request.files['hero_image_file']
            if file and file.filename:
                if section.hero_image:
                    delete_image(section.hero_image)
                section.hero_image = save_uploaded_image(file, 'sections')
        if request.form.get('delete_hero_image') == 'on':
            if section.hero_image:
                delete_image(section.hero_image)
            section.hero_image = ''
        
        section.title = request.form.get('title', '').strip()
        section.h1 = request.form.get('h1', '').strip()
        section.hero_title = request.form.get('hero_title', '').strip()
        section.hero_subtitle = request.form.get('hero_subtitle', '').strip()
        section.content_html = sanitize_html(request.form.get('content_html', ''))
        section.seo_title = request.form.get('seo_title', '')
        section.seo_description = request.form.get('seo_description', '')
        section.seo_text_html = sanitize_html(request.form.get('seo_text_html', ''))
        section.gallery_interval = int(request.form.get('gallery_interval', 5) or 5)
        
        if section_key == 'index':
            delete_ids = request.form.getlist('delete_gallery[]')
            for del_id in delete_ids:
                img = HomeGalleryImage.query.get(int(del_id))
                if img:
                    delete_image(img.image_path)
                    db.session.delete(img)
            
            files = request.files.getlist('gallery_images')
            max_order = db.session.query(db.func.max(HomeGalleryImage.sort_order)).scalar() or 0
            for i, file in enumerate(files):
                if file and file.filename:
                    img_path = save_uploaded_image(file, 'gallery')
                    if img_path:
                        gimg = HomeGalleryImage(
                            image_path=img_path,
                            sort_order=max_order + i + 1
                        )
                        db.session.add(gimg)
        
        db.session.commit()
        flash(f'Раздел "{section.title}" сохранен', 'success')
        return redirect(url_for('admin.section_edit', section_key=section_key))
    
    gallery_images = []
    if section_key == 'index':
        gallery_images = HomeGalleryImage.query.order_by(HomeGalleryImage.sort_order).all()
    
    return render_template('admin/section_form.html', section=section, section_key=section_key, gallery_images=gallery_images)


@admin_bp.route('/services/')
@login_required
def services_list():
    services = Service.query.order_by(Service.sort_order).all()
    return render_template('admin/services_list.html', services=services)

@admin_bp.route('/services/add/', methods=['GET', 'POST'])
@login_required
def services_add():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        slug = request.form.get('slug', '').strip() or generate_slug(title)
        service = Service(
            title=title, slug=slug,
            content_html=sanitize_html(request.form.get('content_html', '')),
            image_path='',
            seo_title=request.form.get('seo_title', ''),
            seo_description=request.form.get('seo_description', ''),
            h1=request.form.get('h1', '').strip(),
            seo_text_html=sanitize_html(request.form.get('seo_text_html', '')),
            hero_image=request.form.get('hero_image', '').strip(),
            hero_title=request.form.get('hero_title', '').strip(),
            hero_subtitle=request.form.get('hero_subtitle', '').strip(),
            gallery_interval=int(request.form.get('gallery_interval', 5) or 5),
            sort_order=int(request.form.get('sort_order', 0) or 0),
            is_active=request.form.get('is_active') == 'on'
        )
        db.session.add(service)
        db.session.commit()
        
        files = request.files.getlist('gallery_images')
        main_index = int(request.form.get('main_image_index', 0) or 0)
        for i, file in enumerate(files):
            if file and file.filename:
                img_path = save_uploaded_image(file, 'services')
                if img_path:
                    simg = ServiceImage(
                        service_id=service.id,
                        image_path=img_path,
                        is_main=(i == main_index),
                        sort_order=i
                    )
                    db.session.add(simg)
        db.session.commit()
        
        flash('Услуга добавлена', 'success')
        return redirect(url_for('admin.services_list'))
    return render_template('admin/services_form.html', service=None)

@admin_bp.route('/services/<int:id>/edit/', methods=['GET', 'POST'])
@login_required
def services_edit(id):
    service = Service.query.get_or_404(id)
    if request.method == 'POST':
        service.title = request.form.get('title', '').strip()
        service.slug = request.form.get('slug', '').strip() or generate_slug(service.title)
        service.content_html = sanitize_html(request.form.get('content_html', ''))
        service.seo_title = request.form.get('seo_title', '')
        service.seo_description = request.form.get('seo_description', '')
        service.h1 = request.form.get('h1', '').strip()
        service.seo_text_html = sanitize_html(request.form.get('seo_text_html', ''))
        service.hero_image = request.form.get('hero_image', '').strip()
        service.hero_title = request.form.get('hero_title', '').strip()
        service.hero_subtitle = request.form.get('hero_subtitle', '').strip()
        service.gallery_interval = int(request.form.get('gallery_interval', 5) or 5)
        service.sort_order = int(request.form.get('sort_order', 0) or 0)
        service.is_active = request.form.get('is_active') == 'on'
        
        main_image_id = request.form.get('main_image_id')
        if main_image_id:
            ServiceImage.query.filter_by(service_id=service.id).update({'is_main': False})
            img = ServiceImage.query.get(int(main_image_id))
            if img:
                img.is_main = True
        
        delete_ids = request.form.getlist('delete_images[]')
        for did in delete_ids:
            img = ServiceImage.query.get(int(did))
            if img:
                delete_image(img.image_path)
                db.session.delete(img)
        
        files = request.files.getlist('gallery_images')
        max_order = db.session.query(db.func.max(ServiceImage.sort_order)).filter_by(service_id=service.id).scalar() or 0
        for i, file in enumerate(files):
            if file and file.filename:
                img_path = save_uploaded_image(file, 'services')
                if img_path:
                    simg = ServiceImage(
                        service_id=service.id,
                        image_path=img_path,
                        is_main=False,
                        sort_order=max_order + i + 1
                    )
                    db.session.add(simg)
        
        db.session.commit()
        flash('Услуга обновлена', 'success')
        return redirect(url_for('admin.services_edit', id=service.id))
    return render_template('admin/services_form.html', service=service)

@admin_bp.route('/services/<int:id>/delete/', methods=['POST'])
@login_required
def services_delete(id):
    service = Service.query.get_or_404(id)
    for img in service.images.all():
        delete_image(img.image_path)
    db.session.delete(service)
    db.session.commit()
    flash('Услуга удалена', 'success')
    return redirect(url_for('admin.services_list'))


@admin_bp.route('/service-image/<int:image_id>/rotate/', methods=['POST'])
@login_required
def rotate_service_image(image_id):
    from flask import jsonify
    img = ServiceImage.query.get_or_404(image_id)
    data = request.get_json() or {}
    degrees = data.get('degrees', 90)
    
    current = img.rotation or 0
    new_rotation = (current + degrees) % 360
    img.rotation = new_rotation
    db.session.commit()
    
    return jsonify({'success': True, 'rotation': new_rotation})


@admin_bp.route('/gallery/rotate/<int:image_id>/', methods=['POST'])
@login_required
def rotate_gallery_image(image_id):
    img = HomeGalleryImage.query.get_or_404(image_id)
    data = request.get_json() or {}
    degrees = data.get('degrees', 90)
    
    current = img.rotation or 0
    new_rotation = (current + degrees) % 360
    img.rotation = new_rotation
    db.session.commit()
    
    return jsonify({'success': True, 'rotation': new_rotation})


@admin_bp.route('/pages/')
@login_required
def pages_list():
    pages = Page.query.order_by(Page.slug).all()
    return render_template('admin/pages_list.html', pages=pages)


@admin_bp.route('/pages/add/', methods=['GET', 'POST'])
@login_required
def pages_add():
    if request.method == 'POST':
        slug = request.form.get('slug', '').strip()
        url_path = request.form.get('url_path', '').strip()
        if not url_path.startswith('/'):
            url_path = '/' + url_path
        if not url_path.endswith('/'):
            url_path = url_path + '/'
        
        page = Page(
            slug=slug,
            url_path=url_path,
            title=request.form.get('title', ''),
            content_html=sanitize_html(request.form.get('content_html', '')),
            seo_title=request.form.get('seo_title', ''),
            seo_description=request.form.get('seo_description', ''),
            h1=request.form.get('h1', '').strip(),
            seo_text_html=sanitize_html(request.form.get('seo_text_html', '')),
            hero_image=request.form.get('hero_image', '').strip(),
            hero_title=request.form.get('hero_title', '').strip(),
            hero_subtitle=request.form.get('hero_subtitle', '').strip(),
            is_published=request.form.get('is_published') == 'on'
        )
        db.session.add(page)
        db.session.commit()
        flash('Страница создана', 'success')
        return redirect(url_for('admin.pages_list'))
    
    return render_template('admin/pages_form.html', page=None)


@admin_bp.route('/pages/<int:id>/edit/', methods=['GET', 'POST'])
@login_required
def pages_edit(id):
    page = Page.query.get_or_404(id)
    
    if request.method == 'POST':
        page.slug = request.form.get('slug', '').strip()
        url_path = request.form.get('url_path', '').strip()
        if not url_path.startswith('/'):
            url_path = '/' + url_path
        if not url_path.endswith('/'):
            url_path = url_path + '/'
        page.url_path = url_path
        page.title = request.form.get('title', '')
        page.content_html = sanitize_html(request.form.get('content_html', ''))
        page.seo_title = request.form.get('seo_title', '')
        page.seo_description = request.form.get('seo_description', '')
        page.h1 = request.form.get('h1', '')
        page.seo_text_html = sanitize_html(request.form.get('seo_text_html', ''))
        page.hero_image = request.form.get('hero_image', '')
        page.hero_title = request.form.get('hero_title', '')
        page.hero_subtitle = request.form.get('hero_subtitle', '')
        page.is_published = request.form.get('is_published') == 'on'
        db.session.commit()
        flash('Страница обновлена', 'success')
        return redirect(url_for('admin.pages_list'))
    
    return render_template('admin/pages_form.html', page=page)


@admin_bp.route('/pages/<int:id>/delete/', methods=['POST'])
@login_required
def pages_delete(id):
    page = Page.query.get_or_404(id)
    db.session.delete(page)
    db.session.commit()
    flash('Страница удалена', 'success')
    return redirect(url_for('admin.pages_list'))


@admin_bp.route('/menu/')
@login_required
def menu_list():
    items = MenuItem.query.order_by(MenuItem.sort_order).all()
    return render_template('admin/menu_list.html', items=items)


@admin_bp.route('/menu/add/', methods=['GET', 'POST'])
@login_required
def menu_add():
    if request.method == 'POST':
        hero_image = ''
        if 'hero_image_file' in request.files:
            file = request.files['hero_image_file']
            if file and file.filename:
                hero_image = save_uploaded_image(file, 'hero', max_size=(1920, 1080))
        
        item = MenuItem(
            title=request.form.get('title', ''),
            url=request.form.get('url', ''),
            sort_order=int(request.form.get('sort_order', 0) or 0),
            is_active=request.form.get('is_active') == 'on',
            is_external=request.form.get('is_external') == 'on',
            nofollow=request.form.get('nofollow') == 'on',
            target_blank=request.form.get('target_blank') == 'on',
            hero_image=hero_image or request.form.get('hero_image', ''),
            hero_title=request.form.get('hero_title', ''),
            hero_subtitle=request.form.get('hero_subtitle', '')
        )
        db.session.add(item)
        db.session.commit()
        flash('Пункт меню создан', 'success')
        return redirect(url_for('admin.menu_list'))
    
    return render_template('admin/menu_form.html', item=None)


@admin_bp.route('/menu/<int:id>/edit/', methods=['GET', 'POST'])
@login_required
def menu_edit(id):
    item = MenuItem.query.get_or_404(id)
    
    if request.method == 'POST':
        if 'hero_image_file' in request.files:
            file = request.files['hero_image_file']
            if file and file.filename:
                if item.hero_image:
                    delete_image(item.hero_image)
                item.hero_image = save_uploaded_image(file, 'hero', max_size=(1920, 1080))
        
        if request.form.get('delete_hero_image') == 'on':
            if item.hero_image:
                delete_image(item.hero_image)
            item.hero_image = ''
        
        item.title = request.form.get('title', '')
        item.url = request.form.get('url', '')
        item.sort_order = int(request.form.get('sort_order', 0) or 0)
        item.is_active = request.form.get('is_active') == 'on'
        item.is_external = request.form.get('is_external') == 'on'
        item.nofollow = request.form.get('nofollow') == 'on'
        item.target_blank = request.form.get('target_blank') == 'on'
        item.hero_title = request.form.get('hero_title', '')
        item.hero_subtitle = request.form.get('hero_subtitle', '')
        db.session.commit()
        flash('Пункт меню обновлён', 'success')
        return redirect(url_for('admin.menu_list'))
    
    return render_template('admin/menu_form.html', item=item)


@admin_bp.route('/menu/<int:id>/delete/', methods=['POST'])
@login_required
def menu_delete(id):
    item = MenuItem.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Пункт меню удалён', 'success')
    return redirect(url_for('admin.menu_list'))


@admin_bp.route('/categories/')
@login_required
def categories_list():
    categories = Category.query.order_by(Category.sort_order).all()
    return render_template('admin/categories_list.html', categories=categories)


@admin_bp.route('/categories/add/', methods=['GET', 'POST'])
@login_required
def categories_add():
    if request.method == 'POST':
        slug = request.form.get('slug', '').strip()
        
        if is_reserved_slug(slug):
            flash(f'Slug "{slug}" зарезервирован системой', 'danger')
            return render_template('admin/categories_form.html', category=None)
        
        image_path = ''
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename:
                image_path = save_uploaded_image(file, 'categories')
        
        cat = Category(
            name=request.form.get('name', ''),
            slug=slug,
            description_html=sanitize_html(request.form.get('description_html', '')),
            image_path=image_path or request.form.get('image_path', ''),
            seo_title=request.form.get('seo_title', ''),
            seo_description=request.form.get('seo_description', ''),
            h1=request.form.get('h1', '').strip(),
            seo_text_html=sanitize_html(request.form.get('seo_text_html', '')),
            hero_image=request.form.get('hero_image', '').strip(),
            hero_title=request.form.get('hero_title', '').strip(),
            hero_subtitle=request.form.get('hero_subtitle', '').strip(),
            sort_order=int(request.form.get('sort_order', 0) or 0),
            is_active=request.form.get('is_active') == 'on'
        )
        db.session.add(cat)
        db.session.commit()
        flash('Категория создана', 'success')
        return redirect(url_for('admin.categories_list'))
    
    return render_template('admin/categories_form.html', category=None)


@admin_bp.route('/categories/<int:id>/edit/', methods=['GET', 'POST'])
@login_required
def categories_edit(id):
    cat = Category.query.get_or_404(id)
    
    if request.method == 'POST':
        slug = request.form.get('slug', '').strip()
        
        if is_reserved_slug(slug):
            flash(f'Slug "{slug}" зарезервирован системой', 'danger')
            return render_template('admin/categories_form.html', category=cat)
        
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename:
                if cat.image_path:
                    delete_image(cat.image_path)
                cat.image_path = save_uploaded_image(file, 'categories')
        
        if request.form.get('delete_image') == 'on':
            if cat.image_path:
                delete_image(cat.image_path)
            cat.image_path = ''
        
        cat.name = request.form.get('name', '')
        cat.slug = slug
        cat.description_html = sanitize_html(request.form.get('description_html', ''))
        cat.seo_title = request.form.get('seo_title', '')
        cat.seo_description = request.form.get('seo_description', '')
        cat.h1 = request.form.get('h1', '')
        cat.seo_text_html = sanitize_html(request.form.get('seo_text_html', ''))
        cat.hero_image = request.form.get('hero_image', '')
        cat.hero_title = request.form.get('hero_title', '')
        cat.hero_subtitle = request.form.get('hero_subtitle', '')
        cat.sort_order = int(request.form.get('sort_order', 0) or 0)
        cat.is_active = request.form.get('is_active') == 'on'
        db.session.commit()
        flash('Категория обновлена', 'success')
        return redirect(url_for('admin.categories_list'))
    
    return render_template('admin/categories_form.html', category=cat)


@admin_bp.route('/categories/<int:id>/delete/', methods=['POST'])
@login_required
def categories_delete(id):
    cat = Category.query.get_or_404(id)
    db.session.delete(cat)
    db.session.commit()
    flash('Категория удалена', 'success')
    return redirect(url_for('admin.categories_list'))


@admin_bp.route('/categories/import/', methods=['GET', 'POST'])
@login_required
def categories_import():
    if request.method == 'POST':
        file = request.files.get('csv_file')
        if file:
            results = import_categories_csv(file.read())
            flash(f"Импортировано: {results['success']}. Ошибок: {len(results['errors'])}", 
                  'success' if not results['errors'] else 'warning')
            if results['errors']:
                for err in results['errors'][:5]:
                    flash(err, 'danger')
        return redirect(url_for('admin.categories_list'))
    
    return render_template('admin/import_csv.html', entity='категории', template_type='categories')


@admin_bp.route('/product-lines/')
@login_required
def product_lines_list():
    categories = Category.query.order_by(Category.name).all()
    
    category_id = request.args.get('category_id', '', type=str)
    search = request.args.get('search', '', type=str).strip().lower()
    
    query = ProductLine.query.join(Category)
    
    if category_id:
        query = query.filter(ProductLine.category_id == int(category_id))
    
    if search:
        query = query.filter(
            db.or_(
                Category.name.ilike(f'%{search}%'),
                ProductLine.name.ilike(f'%{search}%')
            )
        )
    
    # Use query instead of ProductLine.query.filter_by
    lines = query.order_by(Category.name, ProductLine.sort_order).all()
    return render_template('admin/product_lines_list.html', 
                           product_lines=lines, 
                           categories=categories,
                           selected_category=category_id,
                           search=request.args.get('search', ''))


@admin_bp.route('/product-lines/add/', methods=['GET', 'POST'])
@login_required
def product_lines_add():
    categories = Category.query.order_by(Category.name).all()
    
    if request.method == 'POST':
        image_path = ''
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename:
                image_path = save_uploaded_image(file, 'products')
        
        pl = ProductLine(
            category_id=int(request.form.get('category_id')),
            name=request.form.get('name', ''),
            slug=request.form.get('slug', '').strip(),
            image_path=image_path or request.form.get('image_path', ''),
            seo_title=request.form.get('seo_title', ''),
            seo_description=request.form.get('seo_description', ''),
            h1=request.form.get('h1', ''),
            seo_text_html=sanitize_html(request.form.get('seo_text_html', '')),
            hero_image=request.form.get('hero_image', '').strip(),
            hero_title=request.form.get('hero_title', '').strip(),
            hero_subtitle=request.form.get('hero_subtitle', '').strip(),
            gallery_interval=int(request.form.get('gallery_interval', 5) or 5),
            discount_percent=float(request.form.get('discount_percent', 0) or 0),
            hide_price=request.form.get('hide_price') == 'on',
            sort_order=int(request.form.get('sort_order', 0) or 0),
            is_active=request.form.get('is_active') == 'on'
        )
        db.session.add(pl)
        db.session.commit()
        flash('Линейка создана. Теперь вы можете добавить изображения в галерею.', 'success')
        return redirect(url_for('admin.product_lines_edit', id=pl.id))
    
    return render_template('admin/product_lines_form.html', product_line=None, categories=categories)


@admin_bp.route('/product-lines/<int:id>/edit/', methods=['GET', 'POST'])
@login_required
def product_lines_edit(id):
    pl = ProductLine.query.get_or_404(id)
    cat = pl.category
    
    # Navigation logic for product lines within the same category
    prev_pl = ProductLine.query.filter(
        ProductLine.category_id == cat.id,
        ProductLine.sort_order < pl.sort_order
    ).order_by(ProductLine.sort_order.desc()).first()
    
    if not prev_pl:
        prev_pl = ProductLine.query.filter(
            ProductLine.category_id == cat.id,
            ProductLine.sort_order == pl.sort_order,
            ProductLine.id < pl.id
        ).order_by(ProductLine.id.desc()).first()
        
    next_pl = ProductLine.query.filter(
        ProductLine.category_id == cat.id,
        ProductLine.sort_order > pl.sort_order
    ).order_by(ProductLine.sort_order.asc()).first()
    
    if not next_pl:
        next_pl = ProductLine.query.filter(
            ProductLine.category_id == cat.id,
            ProductLine.sort_order == pl.sort_order,
            ProductLine.id > pl.id
        ).order_by(ProductLine.id.asc()).first()
    
    categories = Category.query.order_by(Category.name).all()
    
    if request.method == 'POST':
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename:
                if pl.image_path:
                    delete_image(pl.image_path)
                pl.image_path = save_uploaded_image(file, 'products')
        
        if request.form.get('delete_image') == 'on':
            if pl.image_path:
                delete_image(pl.image_path)
            pl.image_path = ''
        
        pl.category_id = int(request.form.get('category_id'))
        pl.name = request.form.get('name', '')
        pl.slug = request.form.get('slug', '').strip()
        pl.seo_title = request.form.get('seo_title', '')
        pl.seo_description = request.form.get('seo_description', '')
        pl.h1 = request.form.get('h1', '')
        pl.seo_text_html = sanitize_html(request.form.get('seo_text_html', ''))
        pl.hero_image = request.form.get('hero_image', '').strip()
        pl.hero_title = request.form.get('hero_title', '').strip()
        pl.hero_subtitle = request.form.get('hero_subtitle', '').strip()
        pl.gallery_interval = int(request.form.get('gallery_interval', 5) or 5)
        pl.discount_percent = float(request.form.get('discount_percent', 0) or 0)
        pl.hide_price = request.form.get('hide_price') == 'on'
        pl.sort_order = int(request.form.get('sort_order', 0) or 0)
        pl.is_active = request.form.get('is_active') == 'on'
        
        main_image_id = request.form.get('main_image_id')
        if main_image_id:
            ProductLineImage.query.filter_by(product_line_id=pl.id).update({'is_main': False})
            img = ProductLineImage.query.get(int(main_image_id))
            if img:
                img.is_main = True
        
        delete_ids = request.form.getlist('delete_images[]')
        for did in delete_ids:
            img = ProductLineImage.query.get(int(did))
            if img:
                delete_image(img.image_path)
                db.session.delete(img)
        
        files = request.files.getlist('gallery_images')
        max_order = db.session.query(db.func.max(ProductLineImage.sort_order)).filter_by(product_line_id=pl.id).scalar() or 0
        for i, file in enumerate(files):
            if file and file.filename:
                img_path = save_uploaded_image(file, 'products')
                if img_path:
                    pimg = ProductLineImage(
                        product_line_id=pl.id,
                        image_path=img_path,
                        is_main=False,
                        sort_order=max_order + i + 1
                    )
                    db.session.add(pimg)
        
        db.session.commit()
        flash('Линейка обновлена', 'success')
        return redirect(url_for('admin.product_lines_edit', id=pl.id))
    
    return render_template('admin/product_lines_form.html', 
                           product_line=pl, 
                           categories=categories,
                           prev_id=prev_pl.id if prev_pl else None,
                           next_id=next_pl.id if next_pl else None)


@admin_bp.route('/product-lines/<int:id>/delete/', methods=['POST'])
@login_required
def product_lines_delete(id):
    pl = ProductLine.query.get_or_404(id)
    db.session.delete(pl)
    db.session.commit()
    flash('Линейка удалена', 'success')
    return redirect(url_for('admin.product_lines_list'))


@admin_bp.route('/product-lines/import/', methods=['GET', 'POST'])
@login_required
def product_lines_import():
    if request.method == 'POST':
        file = request.files.get('csv_file')
        if file:
            results = import_product_lines_csv(file.read())
            flash(f"Импортировано: {results['success']}. Ошибок: {len(results['errors'])}", 
                  'success' if not results['errors'] else 'warning')
            if results['errors']:
                for err in results['errors'][:5]:
                    flash(err, 'danger')
        return redirect(url_for('admin.product_lines_list'))
    
    return render_template('admin/import_csv.html', entity='линейки', template_type='product_lines')


@admin_bp.route('/product-line-image/<int:image_id>/rotate/', methods=['POST'])
@login_required
def rotate_product_line_image(image_id):
    img = ProductLineImage.query.get_or_404(image_id)
    data = request.get_json() or {}
    degrees = data.get('degrees', 90)
    img.rotation = (img.rotation + degrees) % 360
    db.session.commit()
    return jsonify({'success': True, 'rotation': img.rotation})


@admin_bp.route('/api/image/accessory/<int:image_id>/rotate/', methods=['POST'])
@login_required
def rotate_accessory_image(image_id):
    img = AccessoryImage.query.get_or_404(image_id)
    data = request.get_json() or {}
    degrees = data.get('degrees', 90)
    img.rotation = (img.rotation + degrees) % 360
    db.session.commit()
    return jsonify({'success': True, 'rotation': img.rotation})


@admin_bp.route('/product-lines/<int:pl_id>/accessories/')
@login_required
def accessory_blocks_list(pl_id):
    pl = ProductLine.query.get_or_404(pl_id)
    blocks = AccessoryBlock.query.filter_by(product_line_id=pl_id).order_by(AccessoryBlock.sort_order).all()
    return render_template('admin/accessory_blocks_list.html', product_line=pl, blocks=blocks)


@admin_bp.route('/product-lines/<int:pl_id>/accessories/add/', methods=['GET', 'POST'])
@login_required
def accessory_blocks_add(pl_id):
    pl = ProductLine.query.get_or_404(pl_id)
    
    if request.method == 'POST':
        block = AccessoryBlock(
            product_line_id=pl_id,
            name=request.form.get('name', '').strip(),
            description_html=sanitize_html(request.form.get('description_html', '')),
            table_html=sanitize_html(request.form.get('table_html', '')),
            sort_order=int(request.form.get('sort_order', 0) or 0),
            is_active=request.form.get('is_active') == 'on'
        )
        db.session.add(block)
        db.session.flush() # Get block.id
        
        # Handle gallery images
        files = request.files.getlist('gallery_images')
        for file in files:
            if file and file.filename:
                img_path = save_uploaded_image(file, 'accessories')
                if img_path:
                    aimg = AccessoryImage(
                        accessory_block_id=block.id,
                        image_path=img_path
                    )
                    db.session.add(aimg)
        
        db.session.commit()
        flash('Блок комплектующих добавлен', 'success')
        return redirect(url_for('admin.accessory_blocks_edit', id=block.id))
    
    return render_template('admin/accessory_blocks_form.html', product_line=pl, block=None)


@admin_bp.route('/accessories/<int:id>/edit/', methods=['GET', 'POST'])
@login_required
def accessory_blocks_edit(id):
    block = AccessoryBlock.query.get_or_404(id)
    pl = block.product_line
    
    # Navigation
    prev_block = AccessoryBlock.query.filter(
        AccessoryBlock.product_line_id == pl.id,
        AccessoryBlock.sort_order < block.sort_order
    ).order_by(AccessoryBlock.sort_order.desc()).first()
    
    if not prev_block:
        prev_block = AccessoryBlock.query.filter(
            AccessoryBlock.product_line_id == pl.id,
            AccessoryBlock.sort_order == block.sort_order,
            AccessoryBlock.id < block.id
        ).order_by(AccessoryBlock.id.desc()).first()
        
    next_block = AccessoryBlock.query.filter(
        AccessoryBlock.product_line_id == pl.id,
        AccessoryBlock.sort_order > block.sort_order
    ).order_by(AccessoryBlock.sort_order.asc()).first()
    
    if not next_block:
        next_block = AccessoryBlock.query.filter(
            AccessoryBlock.product_line_id == pl.id,
            AccessoryBlock.sort_order == block.sort_order,
            AccessoryBlock.id > block.id
        ).order_by(AccessoryBlock.id.asc()).first()
    
    if request.method == 'POST':
        block.name = request.form.get('name', '').strip()
        block.description_html = sanitize_html(request.form.get('description_html', ''))
        block.table_html = sanitize_html(request.form.get('table_html', ''))
        block.sort_order = int(request.form.get('sort_order', 0) or 0)
        block.is_active = request.form.get('is_active') == 'on'
        
        # SEO for images
        for img in block.images:
            img.alt_text = request.form.get(f'alt_{img.id}', '')
            img.title_text = request.form.get(f'title_{img.id}', '')
            img.caption = request.form.get(f'caption_{img.id}', '')
            img.sort_order = int(request.form.get(f'sort_{img.id}', 0) or 0)
            img.no_watermark = request.form.get(f'no_wm_{img.id}') == 'on'

        # Delete images
        delete_ids = request.form.getlist('delete_images[]')
        for did in delete_ids:
            img = AccessoryImage.query.get(int(did))
            if img:
                delete_image(img.image_path)
                db.session.delete(img)
        
        # Add new images
        files = request.files.getlist('gallery_images')
        for file in files:
            if file and file.filename:
                img_path = save_uploaded_image(file, 'accessories')
                if img_path:
                    aimg = AccessoryImage(
                        accessory_block_id=block.id,
                        image_path=img_path
                    )
                    db.session.add(aimg)
        
        db.session.commit()
        flash('Блок комплектующих обновлен', 'success')
        return redirect(url_for('admin.accessory_blocks_list', pl_id=pl.id))
    
    return render_template('admin/accessory_blocks_form.html', 
                           product_line=pl, 
                           block=block,
                           prev_id=prev_block.id if prev_block else None,
                           next_id=next_block.id if next_block else None)


@admin_bp.route('/accessories/<int:id>/delete/', methods=['POST'])
@login_required
def accessory_blocks_delete(id):
    block = AccessoryBlock.query.get_or_404(id)
    pl_id = block.product_line_id
    if block.image_path:
        delete_image(block.image_path)
    db.session.delete(block)
    db.session.commit()
    flash('Блок комплектующих удален', 'success')
    return redirect(url_for('admin.accessory_blocks_list', pl_id=pl_id))


@admin_bp.route('/size-items/')
@login_required
def size_items_list():
    categories = Category.query.order_by(Category.name).all()
    product_lines = ProductLine.query.join(Category).order_by(Category.name, ProductLine.name).all()
    
    category_id = request.args.get('category_id', '', type=str)
    product_line_id = request.args.get('product_line_id', '', type=str)
    search = request.args.get('search', '', type=str).strip().lower()
    
    query = SizeItem.query.join(ProductLine).join(Category)
    
    if category_id:
        query = query.filter(ProductLine.category_id == int(category_id))
    
    if product_line_id:
        query = query.filter(SizeItem.product_line_id == int(product_line_id))
    
    if search:
        search_filter = db.or_(
            Category.name.ilike(f'%{search}%'),
            ProductLine.name.ilike(f'%{search}%'),
            SizeItem.size_text.ilike(f'%{search}%')
        )
        query = query.filter(search_filter)
    
    items = query.order_by(Category.name, ProductLine.name, SizeItem.size_text).all()
    return render_template('admin/size_items_list.html', 
                           size_items=items,
                           categories=categories,
                           product_lines=product_lines,
                           selected_category=category_id,
                           selected_product_line=product_line_id,
                           search=request.args.get('search', ''))


@admin_bp.route('/size-items/add/', methods=['GET', 'POST'])
@login_required
def size_items_add():
    product_lines = ProductLine.query.join(Category).order_by(Category.name, ProductLine.name).all()
    
    if request.method == 'POST':
        pl_id = int(request.form.get('product_line_id'))
        pl = ProductLine.query.get(pl_id)
        size_text = request.form.get('size_text', '').strip()
        
        discount_str = request.form.get('discount_percent', '').strip()
        discount_val = float(discount_str) if discount_str else None
        
        hide_price_opt = request.form.get('hide_price_option', '')
        if hide_price_opt == 'show':
            hide_price_val = False
        elif hide_price_opt == 'hide':
            hide_price_val = True
        else:
            hide_price_val = None
        
        size_slug = request.form.get('size_slug', '').strip() or size_text.replace('/', '_')
        size_slug = size_slug.replace('Плюс', 'plus')
        auto_sku = f"{pl.slug}-{size_slug}" if pl else size_slug
        auto_sku = auto_sku.replace('Плюс', 'plus')
        
        si = SizeItem(
            product_line_id=pl_id,
            size_text=size_text,
            size_slug=size_slug,
            full_name=f"{pl.name} {size_text}" if pl else size_text,
            sku=auto_sku,
            price=float(request.form.get('price', 0) or 0),
            currency=request.form.get('currency', 'RUB'),
            unit=request.form.get('unit', 'шт'),
            in_stock=request.form.get('in_stock') == 'on',
            image_path=request.form.get('image_path', ''),
            discount_percent=discount_val,
            hide_price=hide_price_val,
            pipe_dxs=request.form.get('pipe_dxs', ''),
            pressure=request.form.get('pressure', ''),
            mass_per_m=request.form.get('mass_per_m', ''),
            min_bend_radius=request.form.get('min_bend_radius', ''),
            max_len_coil=request.form.get('max_len_coil', ''),
            max_len_drum=request.form.get('max_len_drum', '')
        )
        db.session.add(si)
        db.session.commit()
        flash('Типоразмер создан', 'success')
        
        return redirect(url_for('admin.size_items_list', 
                               category_id=request.args.get('category_id'),
                               product_line_id=request.args.get('product_line_id'),
                               search=request.args.get('search')))
    
    return render_template('admin/size_items_form.html', size_item=None, product_lines=product_lines)


@admin_bp.route('/size-items/<int:id>/edit/', methods=['GET', 'POST'])
@login_required
def size_items_edit(id):
    si = SizeItem.query.get_or_404(id)
    pl = si.product_line
    
    # Navigation logic for size items within the same product line
    prev_item = SizeItem.query.filter(
        SizeItem.product_line_id == pl.id,
        SizeItem.id < si.id
    ).order_by(SizeItem.id.desc()).first()
    
    next_item = SizeItem.query.filter(
        SizeItem.product_line_id == pl.id,
        SizeItem.id > si.id
    ).order_by(SizeItem.id.asc()).first()
    
    product_lines = ProductLine.query.join(Category).order_by(Category.name, ProductLine.name).all()
    
    if request.method == 'POST':
        pl_id = int(request.form.get('product_line_id'))
        pl = ProductLine.query.get(pl_id)
        size_text = request.form.get('size_text', '').strip()
        
        discount_str = request.form.get('discount_percent', '').strip()
        discount_val = float(discount_str) if discount_str else None
        
        hide_price_opt = request.form.get('hide_price_option', '')
        if hide_price_opt == 'show':
            hide_price_val = False
        elif hide_price_opt == 'hide':
            hide_price_val = True
        else:
            hide_price_val = None
        
        si.product_line_id = pl_id
        si.size_text = size_text
        
        # Automatic SKU generation if not provided
        user_sku = request.form.get('sku', '').strip()
        if not user_sku:
            size_slug = (request.form.get('size_slug', '').strip() or size_text.replace('/', '_')).replace('Плюс', 'plus')
            si.sku = f"{pl.slug}-{size_slug}".replace('Плюс', 'plus')
        else:
            si.sku = user_sku

        si.size_slug = (request.form.get('size_slug', '').strip() or size_text.replace('/', '_')).replace('Плюс', 'plus')
        si.full_name = f"{pl.name} {size_text}" if pl else size_text
        si.price = float(request.form.get('price', 0) or 0)
        si.currency = request.form.get('currency', 'RUB')
        si.unit = request.form.get('unit', 'шт')
        si.in_stock = request.form.get('in_stock') == 'on'
        si.image_path = request.form.get('image_path', '')
        si.discount_percent = discount_val
        si.hide_price = hide_price_val
        si.pipe_dxs = request.form.get('pipe_dxs', '')
        si.pressure = request.form.get('pressure', '')
        si.mass_per_m = request.form.get('mass_per_m', '')
        si.min_bend_radius = request.form.get('min_bend_radius', '')
        si.max_len_coil = request.form.get('max_len_coil', '')
        si.max_len_drum = request.form.get('max_len_drum', '')
        db.session.commit()
        flash('Типоразмер обновлён', 'success')
        
        return redirect(url_for('admin.size_items_list', 
                               category_id=request.args.get('category_id'),
                               product_line_id=request.args.get('product_line_id'),
                               search=request.args.get('search')))
    
    return render_template('admin/size_items_form.html', 
                           size_item=si, 
                           product_lines=product_lines,
                           prev_id=prev_item.id if prev_item else None,
                           next_id=next_item.id if next_item else None)


@admin_bp.route('/size-items/<int:id>/delete/', methods=['POST'])
@login_required
def size_items_delete(id):
    si = SizeItem.query.get_or_404(id)
    db.session.delete(si)
    db.session.commit()
    flash('Типоразмер удалён', 'success')
    return redirect(url_for('admin.size_items_list', 
                           category_id=request.args.get('category_id'),
                           product_line_id=request.args.get('product_line_id'),
                           search=request.args.get('search')))


@admin_bp.route('/size-items/bulk-delete/', methods=['POST'])
@login_required
def size_items_bulk_delete():
    ids = request.form.getlist('selected_ids[]')
    if ids:
        count = 0
        for id_str in ids:
            si = SizeItem.query.get(int(id_str))
            if si:
                db.session.delete(si)
                count += 1
        db.session.commit()
        flash(f'Удалено типоразмеров: {count}', 'success')
    else:
        flash('Ничего не выбрано', 'warning')
    return redirect(url_for('admin.size_items_list', 
                           category_id=request.args.get('category_id'),
                           product_line_id=request.args.get('product_line_id'),
                           search=request.args.get('search')))


@admin_bp.route('/size-items/import/', methods=['GET', 'POST'])
@login_required
def size_items_import():
    if request.method == 'POST':
        file = request.files.get('csv_file')
        if file:
            results = import_size_items_csv(file.read())
            flash(f"Импортировано: {results['success']}. Ошибок: {len(results['errors'])}", 
                  'success' if not results['errors'] else 'warning')
            if results['errors']:
                for err in results['errors'][:5]:
                    flash(err, 'danger')
        return redirect(url_for('admin.size_items_list', 
                               category_id=request.args.get('category_id'),
                               product_line_id=request.args.get('product_line_id'),
                               search=request.args.get('search')))
    
    return render_template('admin/import_csv.html', entity='типоразмеры', template_type='size_items')


@admin_bp.route('/news/')
@login_required
def news_list():
    news = News.query.order_by(News.date.desc()).all()
    return render_template('admin/news_list.html', news=news)


@admin_bp.route('/news/add/', methods=['GET', 'POST'])
@login_required
def news_add():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        slug = request.form.get('slug', '').strip() or generate_slug(title)
        
        from datetime import datetime
        date_str = request.form.get('date', '')
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.utcnow().date()
        except:
            date = datetime.utcnow().date()
        
        news = News(
            title=title,
            slug=slug,
            date=date,
            content_html=sanitize_html(request.form.get('content_html', '')),
            seo_title=request.form.get('seo_title', ''),
            seo_description=request.form.get('seo_description', ''),
            h1=request.form.get('h1', ''),
            seo_text_html=sanitize_html(request.form.get('seo_text_html', '')),
            is_published=request.form.get('is_published') == 'on'
        )
        db.session.add(news)
        db.session.commit()
        flash('Новость создана', 'success')
        return redirect(url_for('admin.news_list'))
    
    return render_template('admin/news_form.html', news=None)


@admin_bp.route('/news/<int:id>/edit/', methods=['GET', 'POST'])
@login_required
def news_edit(id):
    news = News.query.get_or_404(id)
    
    if request.method == 'POST':
        from datetime import datetime
        date_str = request.form.get('date', '')
        try:
            news.date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else news.date
        except:
            pass
        
        news.title = request.form.get('title', '').strip()
        news.slug = request.form.get('slug', '').strip() or generate_slug(news.title)
        news.content_html = sanitize_html(request.form.get('content_html', ''))
        news.seo_title = request.form.get('seo_title', '')
        news.seo_description = request.form.get('seo_description', '')
        news.h1 = request.form.get('h1', '')
        news.seo_text_html = sanitize_html(request.form.get('seo_text_html', ''))
        news.is_published = request.form.get('is_published') == 'on'
        db.session.commit()
        flash('Новость обновлена', 'success')
        return redirect(url_for('admin.news_list'))
    
    return render_template('admin/news_form.html', news=news)


@admin_bp.route('/news/<int:id>/delete/', methods=['POST'])
@login_required
def news_delete(id):
    news = News.query.get_or_404(id)
    db.session.delete(news)
    db.session.commit()
    flash('Новость удалена', 'success')
    return redirect(url_for('admin.news_list'))


@admin_bp.route('/news/import/', methods=['GET', 'POST'])
@login_required
def news_import():
    if request.method == 'POST':
        file = request.files.get('csv_file')
        if file:
            results = import_news_csv(file.read())
            flash(f"Импортировано: {results['success']}. Ошибок: {len(results['errors'])}", 
                  'success' if not results['errors'] else 'warning')
            if results['errors']:
                for err in results['errors'][:5]:
                    flash(err, 'danger')
        return redirect(url_for('admin.news_list'))
    
    return render_template('admin/import_csv.html', entity='новости', template_type='news')


@admin_bp.route('/documents/')
@login_required
def documents_list():
    docs = DocumentFile.query.order_by(DocumentFile.created_at.desc()).all()
    return render_template('admin/documents_list.html', documents=docs)


@admin_bp.route('/documents/upload/', methods=['GET', 'POST'])
@login_required
def documents_upload():
    if request.method == 'POST':
        file = request.files.get('file')
        title = request.form.get('title', '')
        doc_type = request.form.get('doc_type', 'other')
        
        if file and file.filename:
            filename = secure_filename(file.filename)
            upload_path = os.path.join('static', 'uploads', 'documents')
            os.makedirs(upload_path, exist_ok=True)
            filepath = os.path.join(upload_path, filename)
            file.save(filepath)
            
            doc = DocumentFile(
                title=title or filename,
                file_path=filepath,
                doc_type=doc_type
            )
            db.session.add(doc)
            db.session.commit()
            flash('Документ загружен', 'success')
        return redirect(url_for('admin.documents_list'))
    
    return render_template('admin/documents_form.html')


@admin_bp.route('/documents/<int:id>/delete/', methods=['POST'])
@login_required
def documents_delete(id):
    doc = DocumentFile.query.get_or_404(id)
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    db.session.delete(doc)
    db.session.commit()
    flash('Документ удалён', 'success')
    return redirect(url_for('admin.documents_list'))


@admin_bp.route('/leads/')
@login_required
def leads_list():
    leads = Lead.query.order_by(Lead.created_at.desc()).all()
    return render_template('admin/leads_list.html', leads=leads)


@admin_bp.route('/leads/<int:id>/')
@login_required
def leads_view(id):
    lead = Lead.query.get_or_404(id)
    return render_template('admin/leads_view.html', lead=lead)


@admin_bp.route('/leads/<int:id>/status/', methods=['POST'])
@login_required
def leads_status(id):
    lead = Lead.query.get_or_404(id)
    lead.status = request.form.get('status', 'new')
    db.session.commit()
    flash('Статус обновлён', 'success')
    return redirect(url_for('admin.leads_list'))


@admin_bp.route('/redirects/')
@login_required
def redirects_list():
    redirects = RedirectRule.query.order_by(RedirectRule.created_at.desc()).all()
    return render_template('admin/redirects_list.html', redirects=redirects)


@admin_bp.route('/redirects/add/', methods=['GET', 'POST'])
@login_required
def redirects_add():
    if request.method == 'POST':
        from_path = request.form.get('from_path', '').strip()
        to_path = request.form.get('to_path', '').strip()
        
        if not from_path.startswith('/'):
            from_path = '/' + from_path
        if not from_path.endswith('/'):
            from_path = from_path + '/'
        if not to_path.startswith('/'):
            to_path = '/' + to_path
        
        existing = RedirectRule.query.filter_by(from_path=to_path, to_path=from_path).first()
        if existing:
            flash('Обнаружен цикл редиректов', 'danger')
            return render_template('admin/redirects_form.html', redirect_rule=None)
        
        rule = RedirectRule(
            from_path=from_path,
            to_path=to_path,
            code=int(request.form.get('code', 301)),
            is_active=request.form.get('is_active') == 'on',
            comment=request.form.get('comment', '')
        )
        db.session.add(rule)
        db.session.commit()
        flash('Редирект создан', 'success')
        return redirect(url_for('admin.redirects_list'))
    
    return render_template('admin/redirects_form.html', redirect_rule=None)


@admin_bp.route('/redirects/<int:id>/edit/', methods=['GET', 'POST'])
@login_required
def redirects_edit(id):
    rule = RedirectRule.query.get_or_404(id)
    
    if request.method == 'POST':
        from_path = request.form.get('from_path', '').strip()
        to_path = request.form.get('to_path', '').strip()
        
        if not from_path.startswith('/'):
            from_path = '/' + from_path
        if not from_path.endswith('/'):
            from_path = from_path + '/'
        if not to_path.startswith('/'):
            to_path = '/' + to_path
        
        rule.from_path = from_path
        rule.to_path = to_path
        rule.code = int(request.form.get('code', 301))
        rule.is_active = request.form.get('is_active') == 'on'
        rule.comment = request.form.get('comment', '')
        db.session.commit()
        flash('Редирект обновлён', 'success')
        return redirect(url_for('admin.redirects_list'))
    
    return render_template('admin/redirects_form.html', redirect_rule=rule)


@admin_bp.route('/redirects/<int:id>/delete/', methods=['POST'])
@login_required
def redirects_delete(id):
    rule = RedirectRule.query.get_or_404(id)
    db.session.delete(rule)
    db.session.commit()
    flash('Редирект удалён', 'success')
    return redirect(url_for('admin.redirects_list'))


@admin_bp.route('/settings/')
@login_required
def settings_list():
    settings = Setting.query.order_by(Setting.key).all()
    return render_template('admin/settings_list.html', settings=settings)


@admin_bp.route('/settings/save/', methods=['POST'])
@login_required
def settings_save():
    for key in request.form:
        if key.startswith('setting_'):
            setting_key = key[8:]
            value = request.form.get(key, '')
            
            setting = Setting.query.filter_by(key=setting_key).first()
            if setting:
                setting.value = value
            else:
                setting = Setting(key=setting_key, value=value)
                db.session.add(setting)
    
    db.session.commit()
    flash('Настройки сохранены', 'success')
    return redirect(url_for('admin.settings_list'))


@admin_bp.route('/settings/watermark/upload/', methods=['POST'])
@login_required
def watermark_upload():
    file = request.files.get('watermark')
    if not file or file.filename == '':
        flash('Файл не выбран', 'error')
        return redirect(url_for('admin.settings_list'))
    
    import os
    from werkzeug.utils import secure_filename
    
    upload_dir = os.path.join('static', 'uploads', 'watermark')
    os.makedirs(upload_dir, exist_ok=True)
    
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.png', '.jpg', '.jpeg', '.webp']:
        flash('Неподдерживаемый формат. Используйте PNG, JPG или WebP', 'error')
        return redirect(url_for('admin.settings_list'))
    
    filename = 'watermark' + ext
    filepath = os.path.join(upload_dir, filename)
    
    old_setting = Setting.query.filter_by(key='WATERMARK_IMAGE').first()
    if old_setting and old_setting.value:
        old_path = old_setting.value
        if os.path.exists(old_path):
            os.remove(old_path)
    
    file.save(filepath)
    
    setting = Setting.query.filter_by(key='WATERMARK_IMAGE').first()
    if setting:
        setting.value = filepath
    else:
        setting = Setting(key='WATERMARK_IMAGE', value=filepath)
        db.session.add(setting)
    
    db.session.commit()
    flash('Водяной знак загружен', 'success')
    return redirect(url_for('admin.settings_list'))


@admin_bp.route('/settings/watermark/delete/', methods=['POST'])
@login_required
def watermark_delete():
    import os
    
    setting = Setting.query.filter_by(key='WATERMARK_IMAGE').first()
    if setting and setting.value:
        if os.path.exists(setting.value):
            os.remove(setting.value)
        setting.value = ''
        db.session.commit()
        flash('Водяной знак удалён', 'success')
    else:
        flash('Водяной знак не найден', 'error')
    
    return redirect(url_for('admin.settings_list'))


from services.image_utils import get_image_info, optimize_image, rename_image_file


@admin_bp.route('/api/image/<image_type>/<int:image_id>/info/')
@login_required
def api_image_info(image_type, image_id):
    """Get image info including dimensions and file size."""
    model_map = {
        'home': HomeGalleryImage,
        'service': ServiceImage,
        'product_line': ProductLineImage,
        'accessory': AccessoryImage
    }
    
    model = model_map.get(image_type)
    if not model:
        return jsonify({'error': 'Invalid image type'}), 400
    
    img = model.query.get_or_404(image_id)
    info = get_image_info(img.image_path)
    
    return jsonify({
        'id': img.id,
        'image_path': img.image_path,
        'alt_text': img.alt_text or '',
        'title_text': img.title_text or '',
        'caption': img.caption or '',
        'info': info
    })


@admin_bp.route('/api/image/<image_type>/<int:image_id>/update/', methods=['POST'])
@login_required
def api_image_update(image_type, image_id):
    """Update image SEO fields."""
    model_map = {
        'home': HomeGalleryImage,
        'service': ServiceImage,
        'product_line': ProductLineImage,
        'accessory': AccessoryImage
    }
    
    model = model_map.get(image_type)
    if not model:
        return jsonify({'error': 'Invalid image type'}), 400
    
    img = model.query.get_or_404(image_id)
    
    data = request.get_json() if request.is_json else request.form
    
    if 'alt_text' in data:
        img.alt_text = data['alt_text']
    if 'title_text' in data:
        img.title_text = data['title_text']
    if 'caption' in data:
        img.caption = data['caption']
    
    db.session.commit()
    return jsonify({'success': True})


@admin_bp.route('/api/image/<image_type>/<int:image_id>/rename/', methods=['POST'])
@login_required
def api_image_rename(image_type, image_id):
    """Rename image file."""
    model_map = {
        'home': HomeGalleryImage,
        'service': ServiceImage,
        'product_line': ProductLineImage,
        'accessory': AccessoryImage
    }
    
    model = model_map.get(image_type)
    if not model:
        return jsonify({'error': 'Invalid image type'}), 400
    
    img = model.query.get_or_404(image_id)
    
    data = request.get_json() if request.is_json else request.form
    new_name = data.get('new_name', '').strip()
    
    if not new_name:
        return jsonify({'error': 'New name is required'}), 400
    
    new_path, error = rename_image_file(img.image_path, new_name)
    if error:
        return jsonify({'error': error}), 400
    
    img.image_path = new_path
    db.session.commit()
    
    return jsonify({'success': True, 'new_path': new_path})


@admin_bp.route('/api/image/<image_type>/<int:image_id>/optimize/', methods=['POST'])
@login_required
def api_image_optimize(image_type, image_id):
    """Optimize image (compress and/or resize)."""
    model_map = {
        'home': HomeGalleryImage,
        'service': ServiceImage,
        'product_line': ProductLineImage,
        'accessory': AccessoryImage
    }
    
    model = model_map.get(image_type)
    if not model:
        return jsonify({'error': 'Invalid image type'}), 400
    
    img = model.query.get_or_404(image_id)
    
    data = request.get_json() if request.is_json else request.form
    quality = int(data.get('quality', 85))
    max_width = int(data.get('max_width', 1920))
    max_height = int(data.get('max_height', 1920))
    convert_to_webp = data.get('convert_to_webp', False)
    if isinstance(convert_to_webp, str):
        convert_to_webp = convert_to_webp.lower() in ('true', '1', 'on')
    
    new_path, error = optimize_image(
        img.image_path,
        quality=quality,
        max_width=max_width,
        max_height=max_height,
        convert_to_webp=convert_to_webp
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    if new_path != img.image_path:
        old_path = img.image_path.lstrip('/')
        img.image_path = new_path
        db.session.commit()
        if os.path.exists(old_path) and new_path.lstrip('/') != old_path:
            try:
                os.remove(old_path)
                current_app.logger.info(f"Deleted old image: {old_path}")
            except Exception as e:
                current_app.logger.error(f"Failed to delete old image {old_path}: {e}")
    
    info = get_image_info(new_path)
    return jsonify({'success': True, 'new_path': new_path, 'info': info})


@admin_bp.route('/api/image/<image_type>/<int:image_id>/toggle-watermark/', methods=['POST'])
@login_required
def api_image_toggle_watermark(image_type, image_id):
    """Toggle no_watermark flag for image."""
    model_map = {
        'home': HomeGalleryImage,
        'service': ServiceImage,
        'product_line': ProductLineImage,
        'accessory': AccessoryImage
    }
    
    model = model_map.get(image_type)
    if not model:
        return jsonify({'error': 'Invalid image type'}), 400
    
    img = model.query.get_or_404(image_id)
    
    data = request.get_json() if request.is_json else request.form
    no_watermark = data.get('no_watermark', False)
    if isinstance(no_watermark, str):
        no_watermark = no_watermark.lower() in ('true', '1', 'on')
    
    img.no_watermark = no_watermark
    db.session.commit()
    
    return jsonify({'success': True, 'no_watermark': img.no_watermark})


from services.backup_service import export_database, import_database
from datetime import datetime as dt


@admin_bp.route('/settings/backup/download/')
@login_required
def backup_download():
    """Download database backup as JSON file."""
    json_data = export_database()
    filename = f"glavtrubtorg_backup_{dt.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    response = make_response(json_data)
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@admin_bp.route('/settings/backup/upload/', methods=['POST'])
@login_required
def backup_upload():
    """Upload and restore database from JSON backup."""
    file = request.files.get('backup_file')
    if not file or file.filename == '':
        flash('Файл не выбран', 'error')
        return redirect(url_for('admin.settings_list'))
    
    if not file.filename.endswith('.json'):
        flash('Разрешены только JSON файлы', 'error')
        return redirect(url_for('admin.settings_list'))
    
    try:
        json_data = file.read().decode('utf-8')
    except Exception as e:
        flash(f'Ошибка чтения файла: {str(e)}', 'error')
        return redirect(url_for('admin.settings_list'))
    
    clear_existing = request.form.get('clear_existing') == 'on'
    
    success, result = import_database(json_data, clear_existing=clear_existing)
    
    if success:
        total_imported = sum(r.get('imported', 0) for r in result.values())
        total_updated = sum(r.get('updated', 0) for r in result.values())
        flash(f'Импорт завершён: {total_imported} новых, {total_updated} обновлено', 'success')
    else:
        flash(f'Ошибка импорта: {result}', 'error')
    
    return redirect(url_for('admin.settings_list'))

