from flask import request, url_for
from config import Config


def get_absolute_url(path):
    base_url = Config.SITE_URL.rstrip('/')
    if not path.startswith('/'):
        path = '/' + path
    return base_url + path


def generate_seo_title(h1, custom_title=None):
    if custom_title:
        return custom_title
    return f"{h1} — купить, цена, характеристики | {Config.SITE_NAME}"


def generate_seo_description(h1, custom_desc=None):
    if custom_desc:
        return custom_desc
    return f"Актуальные цены и наличие. {h1}. Доставка, консультация. {Config.SITE_NAME}."


def get_page_seo(entity, default_h1=''):
    h1 = getattr(entity, 'h1', '') or getattr(entity, 'title', '') or getattr(entity, 'name', '') or default_h1
    seo_title = getattr(entity, 'seo_title', '') or generate_seo_title(h1)
    seo_description = getattr(entity, 'seo_description', '') or generate_seo_description(h1)
    
    return {
        'title': seo_title,
        'description': seo_description,
        'h1': h1,
        'seo_text': getattr(entity, 'seo_text_html', ''),
    }


def get_canonical_url(path=None):
    if path is None:
        path = request.path
    if not path.endswith('/') and not path.endswith('.xml') and not path.endswith('.txt'):
        path = path + '/'
    return get_absolute_url(path)


def get_og_tags(title, description, url=None, image=None):
    if url is None:
        url = get_canonical_url()
    
    og = {
        'og:title': title,
        'og:description': description,
        'og:url': url,
        'og:type': 'website',
        'og:site_name': Config.SITE_NAME,
    }
    
    if image:
        og['og:image'] = get_absolute_url(image) if not image.startswith('http') else image
    
    return og
