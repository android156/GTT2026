from flask import Blueprint, render_template, abort
from blueprints.public import get_hero_for_url
from models import Service
from services.seo import get_page_seo, get_canonical_url, get_og_tags
from services.schema import generate_breadcrumb_jsonld

public_services_bp = Blueprint('public_services', __name__)

@public_services_bp.route('/services/')
def services_list():
    services = Service.query.filter_by(is_active=True).order_by(Service.sort_order).all()
    
    seo = {
        'title': 'Услуги — ГЛАВТРУБТОРГ',
        'description': 'Комплексные услуги: доставка трубного проката и монтаж фитингов. Надежные решения для вашего бизнеса.',
        'h1': 'Наши услуги'
    }
    
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Услуги', 'url': None}
    ]
    
    hero = get_hero_for_url('/services/')
    
    return render_template('public/services_list.html',
                         services=services,
                         seo=seo,
                         hero=hero,
                         breadcrumbs=breadcrumbs,
                         breadcrumbs_jsonld=generate_breadcrumb_jsonld(breadcrumbs),
                         canonical=get_canonical_url('/services/'),
                         og=get_og_tags(seo['title'], seo['description']))

@public_services_bp.route('/services/<slug>/')
def service_detail(slug):
    service = Service.query.filter_by(slug=slug, is_active=True).first_or_404()
    
    seo = get_page_seo(service)
    
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Услуги', 'url': '/services/'},
        {'name': service.title, 'url': None}
    ]
    
    return render_template('public/service_detail.html',
                         service=service,
                         seo=seo,
                         breadcrumbs=breadcrumbs,
                         breadcrumbs_jsonld=generate_breadcrumb_jsonld(breadcrumbs),
                         canonical=get_canonical_url(f'/services/{slug}/'),
                         og=get_og_tags(seo['title'], seo['description']))
