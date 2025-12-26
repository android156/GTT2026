import csv
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models import Category, ProductLine, Page
from services.slug import generate_slug


def parse_url(url):
    match = re.match(r'https://glavtrubtorg\.ru(/.*)', url)
    if not match:
        return None, None, None
    
    path = match.group(1)
    
    if path.startswith('/files/') or path.startswith('/loadfiles/'):
        return 'file', None, None
    
    if '?' in path or '#' in path:
        return 'skip', None, None
    
    catalog_match = re.match(r'^/catalog/([^/]+)/$', path)
    if catalog_match:
        return 'category', catalog_match.group(1), None
    
    product_match = re.match(r'^/catalog/([^/]+)/([^/]+)/$', path)
    if product_match:
        return 'product', product_match.group(1), product_match.group(2)
    
    if path == '/catalog/':
        return 'catalog_main', None, None
    
    page_match = re.match(r'^/([^/]+)/$', path)
    if page_match:
        return 'page', page_match.group(1), None
    
    if path == '/':
        return 'home', None, None
    
    services_match = re.match(r'^/services/([^/]+)/$', path)
    if services_match:
        return 'service_page', services_match.group(1), None
    
    return 'unknown', path, None


def clean_text(text):
    if not text or text == '<ПУСТО>' or text == '<ОТСУТСТВУЕТ>':
        return ''
    text = text.replace('&ndash;', '–')
    text = text.replace('&mdash;', '—')
    text = text.replace('&nbsp;', ' ')
    return text.strip()


def import_url_inventory(csv_path):
    app = create_app()
    
    with app.app_context():
        categories_created = 0
        products_created = 0
        pages_updated = 0
        
        category_map = {}
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            next(reader)
            
            rows = list(reader)
        
        for row in rows:
            if len(row) < 6:
                continue
            
            url = row[1]
            title = clean_text(row[2])
            description = clean_text(row[3])
            keywords = clean_text(row[4])
            h1 = clean_text(row[5])
            
            if not url:
                continue
            
            url_type, slug1, slug2 = parse_url(url)
            
            if url_type == 'category':
                existing = Category.query.filter_by(slug=slug1).first()
                if not existing:
                    category = Category(
                        name=h1 or title,
                        slug=slug1,
                        description_html=f'<p>{description}</p>' if description else '',
                        seo_title=title,
                        seo_description=description[:300] if description else '',
                        h1=h1,
                        is_active=True,
                        sort_order=categories_created
                    )
                    db.session.add(category)
                    db.session.flush()
                    category_map[slug1] = category.id
                    categories_created += 1
                    print(f"Category: {h1 or title}")
                else:
                    category_map[slug1] = existing.id
        
        db.session.commit()
        
        for row in rows:
            if len(row) < 6:
                continue
            
            url = row[1]
            title = clean_text(row[2])
            description = clean_text(row[3])
            keywords = clean_text(row[4])
            h1 = clean_text(row[5])
            
            if not url:
                continue
            
            url_type, slug1, slug2 = parse_url(url)
            
            if url_type == 'product':
                category_id = category_map.get(slug1)
                if not category_id:
                    cat = Category.query.filter_by(slug=slug1).first()
                    if cat:
                        category_id = cat.id
                
                if category_id:
                    existing = ProductLine.query.filter_by(slug=slug2, category_id=category_id).first()
                    if not existing:
                        product = ProductLine(
                            name=h1 or title,
                            slug=slug2,
                            category_id=category_id,
                            description_html=f'<p>{description}</p>' if description else '',
                            seo_title=title,
                            seo_description=description[:300] if description else '',
                            h1=h1,
                            is_active=True,
                            sort_order=products_created
                        )
                        db.session.add(product)
                        products_created += 1
                        print(f"  Product: {h1 or title}")
            
            elif url_type == 'page':
                page = Page.query.filter_by(slug=slug1).first()
                if page:
                    page.seo_title = title or page.seo_title
                    page.seo_description = description[:300] if description else page.seo_description
                    page.h1 = h1 or page.h1
                    pages_updated += 1
                    print(f"Page updated: {slug1}")
        
        db.session.commit()
        
        print(f"\n=== Import Complete ===")
        print(f"Categories created: {categories_created}")
        print(f"Products created: {products_created}")
        print(f"Pages updated: {pages_updated}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python import_url_inventory.py <csv_file>")
        sys.exit(1)
    
    import_url_inventory(sys.argv[1])
