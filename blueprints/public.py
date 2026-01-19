from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, Response, send_file, make_response
from extensions import db
from models import Page, MenuItem, Category, ProductLine, SizeItem, News, Lead, Setting, Service, SiteSection, HomeGalleryImage, ProductLineImage, AccessoryBlock, ServiceImage
from services.seo import get_page_seo, get_canonical_url, get_og_tags
from services.schema import generate_product_jsonld, generate_breadcrumb_jsonld, generate_organization_jsonld
from services.image_utils import get_watermarked_image_bytes
from config import RESERVED_SLUGS, Config
from datetime import datetime
import os
import io

public_bp = Blueprint('public', __name__)


def get_menu_items():
    return MenuItem.query.filter_by(is_active=True).order_by(MenuItem.sort_order).all()


def get_hero_for_url(url):
    menu_item = MenuItem.query.filter_by(url=url, is_active=True).first()
    if menu_item and menu_item.hero_image:
        return {
            'image': menu_item.hero_image,
            'title': menu_item.hero_title or menu_item.title,
            'subtitle': menu_item.hero_subtitle
        }
    return None


def get_hero_for_section(section_key):
    section = SiteSection.query.filter_by(section_key=section_key).first()
    if section and section.hero_image:
        return {
            'image': section.hero_image,
            'title': section.hero_title or section.title,
            'subtitle': section.hero_subtitle
        }
    return None


def get_hero_for_page(page):
    if page and page.hero_image:
        return {
            'image': page.hero_image,
            'title': page.hero_title or page.title,
            'subtitle': page.hero_subtitle
        }
    return get_hero_for_url(page.url_path) if page else None


def get_hero_for_category(category):
    if category and category.hero_image:
        return {
            'image': category.hero_image,
            'title': category.hero_title or category.name,
            'subtitle': category.hero_subtitle
        }
    if category and category.image_path:
        return {
            'image': category.image_path,
            'title': category.hero_title or category.name,
            'subtitle': category.hero_subtitle
        }
    return None


def get_hero_for_service(service):
    if service and service.hero_image:
        return {
            'image': service.hero_image,
            'title': service.hero_title or service.title,
            'subtitle': service.hero_subtitle
        }
    if service and service.image_path:
        return {
            'image': service.image_path,
            'title': service.hero_title or service.title,
            'subtitle': service.hero_subtitle
        }
    return get_hero_for_section('services')


@public_bp.context_processor
def inject_menu():
    return {'menu_items': get_menu_items(), 'site_name': Config.SITE_NAME}


@public_bp.route('/')
def index():
    news = News.query.filter_by(is_published=True).order_by(News.date.desc()).limit(6).all()
    categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order).all()
    services = Service.query.filter_by(is_active=True).order_by(Service.sort_order).limit(4).all()
    section = SiteSection.query.filter_by(section_key='index').first()
    gallery_images = HomeGalleryImage.query.order_by(HomeGalleryImage.sort_order).all()
    
    seo = {
        'title': section.seo_title if section and section.seo_title else f'{Config.SITE_NAME} — трубы, изоляция, комплектующие',
        'description': section.seo_description if section and section.seo_description else f'{Config.SITE_NAME} — продажа труб, изоляционных материалов и комплектующих. Доставка по России.',
        'h1': section.h1 if section and section.h1 else f'Добро пожаловать в {Config.SITE_NAME}'
    }
    
    return render_template('public/index.html',
                         news=news,
                         categories=categories,
                         services=services,
                         section=section,
                         gallery_images=gallery_images,
                         seo=seo,
                         canonical=get_canonical_url('/'),
                         og=get_og_tags(seo['title'], seo['description']),
                         org_jsonld=generate_organization_jsonld())


@public_bp.route('/catalog/')
def catalog():
    categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order).all()
    section = SiteSection.query.filter_by(section_key='catalog').first()
    
    seo = {
        'title': section.seo_title if section and section.seo_title else f'Каталог продукции — {Config.SITE_NAME}',
        'description': section.seo_description if section and section.seo_description else f'Каталог продукции {Config.SITE_NAME}. Трубы, изоляция, комплектующие.',
        'h1': section.h1 if section and section.h1 else 'Каталог продукции'
    }
    
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Каталог', 'url': None}
    ]
    
    hero = get_hero_for_section('catalog') or get_hero_for_url('/catalog/')
    
    return render_template('public/catalog.html',
                         categories=categories,
                         section=section,
                         seo=seo,
                         hero=hero,
                         breadcrumbs=breadcrumbs,
                         breadcrumbs_jsonld=generate_breadcrumb_jsonld(breadcrumbs),
                         canonical=get_canonical_url('/catalog/'),
                         og=get_og_tags(seo['title'], seo['description']))



@public_bp.route('/services/')
def services_list():
    services = Service.query.filter_by(is_active=True).order_by(Service.sort_order).all()
    seo = {
        'title': f'Услуги — {Config.SITE_NAME}',
        'description': f'Услуги компании {Config.SITE_NAME}. Доставка, монтаж и другие сервисы.',
        'h1': 'Наши услуги'
    }
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Услуги', 'url': None}
    ]
    hero = get_hero_for_section('services') or get_hero_for_url('/services/')
    return render_template('public/services.html', 
                         services=services, 
                         seo=seo, 
                         hero=hero,
                         breadcrumbs=breadcrumbs,
                         breadcrumbs_jsonld=generate_breadcrumb_jsonld(breadcrumbs),
                         canonical=get_canonical_url('/services/'),
                         og=get_og_tags(seo['title'], seo['description']))

@public_bp.route('/services/<slug>/')
def service_detail(slug):
    service = Service.query.filter_by(slug=slug, is_active=True).first_or_404()
    seo = get_page_seo(service)
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Услуги', 'url': '/services/'},
        {'name': service.title, 'url': None}
    ]
    hero = get_hero_for_service(service)
    return render_template('public/service_detail.html',
                         service=service,
                         seo=seo,
                         hero=hero,
                         breadcrumbs=breadcrumbs,
                         breadcrumbs_jsonld=generate_breadcrumb_jsonld(breadcrumbs),
                         canonical=get_canonical_url(f'/services/{slug}/'),
                         og=get_og_tags(seo['title'], seo['description']))

@public_bp.route('/news/')
def news_list():
    news = News.query.filter_by(is_published=True).order_by(News.date.desc()).all()
    
    seo = {
        'title': f'Новости — {Config.SITE_NAME}',
        'description': f'Новости компании {Config.SITE_NAME}',
        'h1': 'Новости'
    }
    
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Новости', 'url': None}
    ]
    
    hero = get_hero_for_section('news') or get_hero_for_url('/news/')
    
    return render_template('public/news_list.html',
                         news=news,
                         seo=seo,
                         hero=hero,
                         breadcrumbs=breadcrumbs,
                         breadcrumbs_jsonld=generate_breadcrumb_jsonld(breadcrumbs),
                         canonical=get_canonical_url('/news/'),
                         og=get_og_tags(seo['title'], seo['description']))


@public_bp.route('/news/<slug>/')
def news_detail(slug):
    news_item = News.query.filter_by(slug=slug, is_published=True).first_or_404()
    
    seo = get_page_seo(news_item)
    
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Новости', 'url': '/news/'},
        {'name': news_item.title, 'url': None}
    ]
    
    return render_template('public/news_detail.html',
                         news=news_item,
                         seo=seo,
                         breadcrumbs=breadcrumbs,
                         breadcrumbs_jsonld=generate_breadcrumb_jsonld(breadcrumbs),
                         canonical=get_canonical_url(f'/news/{slug}/'),
                         og=get_og_tags(seo['title'], seo['description']))


@public_bp.route('/<path:url_path>')
def static_page(url_path):
    url_path = '/' + url_path.strip('/')  + '/'
    
    page = Page.query.filter_by(url_path=url_path, is_published=True).first()
    
    if page:
        seo = get_page_seo(page)
        
        breadcrumbs = [
            {'name': 'Главная', 'url': '/'},
            {'name': page.title, 'url': None}
        ]
        
        hero = get_hero_for_page(page) or get_hero_for_url(url_path)
        
        return render_template('public/page.html',
                             page=page,
                             seo=seo,
                             hero=hero,
                             breadcrumbs=breadcrumbs,
                             breadcrumbs_jsonld=generate_breadcrumb_jsonld(breadcrumbs),
                             canonical=get_canonical_url(url_path),
                             og=get_og_tags(seo['title'], seo['description']))
    
    parts = url_path.strip('/').split('/')
    
    if len(parts) >= 1:
        category_slug = parts[0]
        
        if category_slug in RESERVED_SLUGS:
            abort(404)
        
        category = Category.query.filter_by(slug=category_slug, is_active=True).first()
        
        if category:
            if len(parts) == 1:
                return render_category(category)
            elif len(parts) == 2:
                product_slug = parts[1]
                product_line = ProductLine.query.filter_by(
                    category_id=category.id, 
                    slug=product_slug, 
                    is_active=True
                ).first_or_404()
                return render_product_line(category, product_line)
            elif len(parts) == 3:
                product_slug = parts[1]
                size_slug = parts[2]
                product_line = ProductLine.query.filter_by(
                    category_id=category.id, 
                    slug=product_slug, 
                    is_active=True
                ).first_or_404()
                size_item = SizeItem.query.filter_by(
                    product_line_id=product_line.id, 
                    size_slug=size_slug
                ).first_or_404()
                return render_size_item(category, product_line, size_item)
    
    abort(404)


def render_category(category):
    product_lines = ProductLine.query.filter_by(
        category_id=category.id, 
        is_active=True
    ).order_by(ProductLine.sort_order).all()
    
    seo = get_page_seo(category)
    hero = get_hero_for_category(category)
    
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Каталог', 'url': '/catalog/'},
        {'name': category.name, 'url': None}
    ]
    
    return render_template('public/category.html',
                         category=category,
                         product_lines=product_lines,
                         seo=seo,
                         hero=hero,
                         breadcrumbs=breadcrumbs,
                         breadcrumbs_jsonld=generate_breadcrumb_jsonld(breadcrumbs),
                         canonical=get_canonical_url(f'/{category.slug}/'),
                         og=get_og_tags(seo['title'], seo['description']))


def get_size_sort_key(size_item):
    """Extract numbers from size_text for numeric sorting (e.g., '110/145' -> (110, 145))"""
    try:
        parts = size_item.size_text.split('/')
        first = int(''.join(c for c in parts[0] if c.isdigit()) or 0)
        second = int(''.join(c for c in parts[1] if c.isdigit()) or 0) if len(parts) > 1 else 0
        return (first, second)
    except (ValueError, AttributeError, IndexError):
        return (0, 0)

def render_product_line(category, product_line):
    size_items = SizeItem.query.filter_by(
        product_line_id=product_line.id
    ).all()
    size_items.sort(key=get_size_sort_key)
    
    gallery_images = ProductLineImage.query.filter_by(
        product_line_id=product_line.id
    ).order_by(ProductLineImage.sort_order).all()
    
    accessory_blocks = AccessoryBlock.query.filter_by(
        product_line_id=product_line.id,
        is_active=True
    ).order_by(AccessoryBlock.sort_order).all()
    
    seo = get_page_seo(product_line)
    
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Каталог', 'url': '/catalog/'},
        {'name': category.name, 'url': f'/{category.slug}/'},
        {'name': product_line.name, 'url': None}
    ]
    
    return render_template('public/product_line.html',
                         category=category,
                         product_line=product_line,
                         size_items=size_items,
                         gallery_images=gallery_images,
                         accessory_blocks=accessory_blocks,
                         seo=seo,
                         breadcrumbs=breadcrumbs,
                         breadcrumbs_jsonld=generate_breadcrumb_jsonld(breadcrumbs),
                         canonical=get_canonical_url(f'/{category.slug}/{product_line.slug}/'),
                         og=get_og_tags(seo['title'], seo['description']))


def render_size_item(category, product_line, size_item):
    seo = {
        'title': size_item.full_name or f"{product_line.name} {size_item.size_text}",
        'description': f"Купить {size_item.full_name or product_line.name} {size_item.size_text}. Цена, характеристики, наличие. {Config.SITE_NAME}.",
        'h1': size_item.full_name or f"{product_line.name} {size_item.size_text}"
    }
    
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Каталог', 'url': '/catalog/'},
        {'name': category.name, 'url': f'/{category.slug}/'},
        {'name': product_line.name, 'url': f'/{category.slug}/{product_line.slug}/'},
        {'name': size_item.size_text, 'url': None}
    ]
    
    product_jsonld = generate_product_jsonld(size_item, product_line, category)
    
    return render_template('public/size_item.html',
                         category=category,
                         product_line=product_line,
                         size_item=size_item,
                         seo=seo,
                         breadcrumbs=breadcrumbs,
                         breadcrumbs_jsonld=generate_breadcrumb_jsonld(breadcrumbs),
                         product_jsonld=product_jsonld,
                         canonical=get_canonical_url(f'/{category.slug}/{product_line.slug}/{size_item.size_slug}/'),
                         og=get_og_tags(seo['title'], seo['description']))


@public_bp.route('/lead/', methods=['POST'])
def submit_lead():
    name = request.form.get('name', '')
    phone = request.form.get('phone', '')
    email = request.form.get('email', '')
    message = request.form.get('message', '')
    
    lead = Lead(
        name=name,
        phone=phone,
        email=email,
        message=message,
        source='site',
        status='new'
    )
    db.session.add(lead)
    db.session.commit()
    
    flash('Заявка успешно отправлена! Мы свяжемся с вами в ближайшее время.', 'success')
    
    referer = request.referrer or url_for('public.index')
    return redirect(referer)


@public_bp.route('/sitemap.xml')
def sitemap():
    pages = []
    
    static_pages = Page.query.filter_by(is_published=True).all()
    for page in static_pages:
        pages.append({
            'loc': get_canonical_url(page.url_path),
            'lastmod': page.updated_at.strftime('%Y-%m-%d') if page.updated_at else None,
            'priority': '0.8'
        })
    
    pages.append({
        'loc': get_canonical_url('/'),
        'priority': '1.0'
    })
    pages.append({
        'loc': get_canonical_url('/catalog/'),
        'priority': '0.9'
    })
    pages.append({
        'loc': get_canonical_url('/news/'),
        'priority': '0.7'
    })
    
    categories = Category.query.filter_by(is_active=True).all()
    for cat in categories:
        pages.append({
            'loc': get_canonical_url(f'/{cat.slug}/'),
            'priority': '0.8'
        })
        
        for pl in cat.product_lines.filter_by(is_active=True):
            pages.append({
                'loc': get_canonical_url(f'/{cat.slug}/{pl.slug}/'),
                'priority': '0.7'
            })
            
            for si in pl.size_items:
                pages.append({
                    'loc': get_canonical_url(f'/{cat.slug}/{pl.slug}/{si.size_slug}/'),
                    'lastmod': si.updated_at.strftime('%Y-%m-%d') if si.updated_at else None,
                    'priority': '0.6'
                })
    
    news = News.query.filter_by(is_published=True).all()
    for n in news:
        pages.append({
            'loc': get_canonical_url(f'/news/{n.slug}/'),
            'lastmod': n.date.strftime('%Y-%m-%d') if n.date else None,
            'priority': '0.5'
        })
    
    sitemap_xml = render_template('sitemap.xml', pages=pages)
    return Response(sitemap_xml, mimetype='application/xml')


@public_bp.route('/robots.txt')
def robots():
    from services.seo import get_absolute_url
    robots_txt = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /login/
Disallow: /logout/

Sitemap: {get_absolute_url('/sitemap.xml')}
"""
    return Response(robots_txt, mimetype='text/plain')


@public_bp.route('/wm/<image_type>/<int:image_id>/')
def watermarked_image(image_type, image_id):
    """Serve gallery image with watermark applied."""
    model_map = {
        'home': HomeGalleryImage,
        'service': ServiceImage,
        'product_line': ProductLineImage
    }
    
    model = model_map.get(image_type)
    if not model:
        abort(404)
    
    img = model.query.get(image_id)
    if not img:
        abort(404)
    
    if img.no_watermark:
        full_path = img.image_path.lstrip('/')
        if os.path.exists(full_path):
            return send_file(full_path)
        abort(404)
    
    watermark_setting = Setting.query.filter_by(key='WATERMARK_IMAGE').first()
    if not watermark_setting or not watermark_setting.value:
        full_path = img.image_path.lstrip('/')
        if os.path.exists(full_path):
            return send_file(full_path)
        abort(404)
    
    opacity_setting = Setting.query.filter_by(key='WATERMARK_OPACITY').first()
    opacity = float(opacity_setting.value) if opacity_setting and opacity_setting.value else 1.0
    
    ext = os.path.splitext(img.image_path)[1].lower()
    if ext in ('.jpg', '.jpeg'):
        output_format = 'JPEG'
    elif ext == '.png':
        output_format = 'PNG'
    elif ext == '.webp':
        output_format = 'WEBP'
    else:
        output_format = 'JPEG'
    
    image_bytes, content_type = get_watermarked_image_bytes(
        img.image_path, 
        watermark_setting.value, 
        output_format,
        opacity
    )
    
    if image_bytes:
        response = make_response(image_bytes)
        response.headers['Content-Type'] = content_type
        response.headers['Cache-Control'] = 'public, max-age=86400'
        return response
    
    full_path = img.image_path.lstrip('/')
    if os.path.exists(full_path):
        return send_file(full_path)
    abort(404)
