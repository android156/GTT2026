import csv
import io
from datetime import datetime
from extensions import db
from models import Category, ProductLine, SizeItem, News
from services.slug import generate_slug, make_unique_slug


def decode_csv_content(file_content):
    """Decode CSV content trying UTF-8 first, then Windows-1251"""
    try:
        return file_content.decode('utf-8-sig')
    except UnicodeDecodeError:
        pass
    try:
        return file_content.decode('cp1251')
    except UnicodeDecodeError:
        pass
    return file_content.decode('utf-8', errors='replace')


def import_categories_csv(file_content):
    results = {'success': 0, 'errors': []}
    
    try:
        stream = io.StringIO(decode_csv_content(file_content))
        reader = csv.DictReader(stream, delimiter=';')
        
        for row_num, row in enumerate(reader, 2):
            try:
                slug = row.get('slug', '').strip()
                name = row.get('name', '').strip()
                
                if not slug and name:
                    slug = generate_slug(name)
                
                if not slug or not name:
                    results['errors'].append(f"Строка {row_num}: пустой slug или name")
                    continue
                
                existing = Category.query.filter_by(slug=slug).first()
                if existing:
                    existing.name = name
                    existing.description_html = row.get('description_html', '')
                    existing.image_path = row.get('image_path', '')
                    existing.seo_title = row.get('seo_title', '')
                    existing.seo_description = row.get('seo_description', '')
                    existing.h1 = row.get('h1', '')
                    existing.seo_text_html = row.get('seo_text_html', '')
                    existing.sort_order = int(row.get('sort_order', 0) or 0)
                    existing.is_active = row.get('is_active', '1').lower() in ['1', 'true', 'yes']
                else:
                    cat = Category(
                        slug=slug,
                        name=name,
                        description_html=row.get('description_html', ''),
                        image_path=row.get('image_path', ''),
                        seo_title=row.get('seo_title', ''),
                        seo_description=row.get('seo_description', ''),
                        h1=row.get('h1', ''),
                        seo_text_html=row.get('seo_text_html', ''),
                        sort_order=int(row.get('sort_order', 0) or 0),
                        is_active=row.get('is_active', '1').lower() in ['1', 'true', 'yes']
                    )
                    db.session.add(cat)
                
                results['success'] += 1
            except Exception as e:
                results['errors'].append(f"Строка {row_num}: {str(e)}")
        
        db.session.commit()
    except Exception as e:
        results['errors'].append(f"Ошибка парсинга CSV: {str(e)}")
    
    return results


def import_product_lines_csv(file_content):
    results = {'success': 0, 'errors': []}
    
    try:
        stream = io.StringIO(decode_csv_content(file_content))
        reader = csv.DictReader(stream, delimiter=';')
        
        for row_num, row in enumerate(reader, 2):
            try:
                category_slug = row.get('category_slug', '').strip()
                slug = row.get('slug', '').strip()
                name = row.get('name', '').strip()
                
                if not slug and name:
                    slug = generate_slug(name)
                
                if not category_slug or not slug or not name:
                    results['errors'].append(f"Строка {row_num}: пустые обязательные поля")
                    continue
                
                category = Category.query.filter_by(slug=category_slug).first()
                if not category:
                    results['errors'].append(f"Строка {row_num}: категория {category_slug} не найдена")
                    continue
                
                existing = ProductLine.query.filter_by(category_id=category.id, slug=slug).first()
                if existing:
                    existing.name = name
                    existing.description_html = row.get('description_html', '')
                    existing.image_path = row.get('image_path', '')
                    existing.seo_title = row.get('seo_title', '')
                    existing.seo_description = row.get('seo_description', '')
                    existing.h1 = row.get('h1', '')
                    existing.seo_text_html = row.get('seo_text_html', '')
                    existing.sort_order = int(row.get('sort_order', 0) or 0)
                    existing.is_active = row.get('is_active', '1').lower() in ['1', 'true', 'yes']
                else:
                    pl = ProductLine(
                        category_id=category.id,
                        slug=slug,
                        name=name,
                        description_html=row.get('description_html', ''),
                        image_path=row.get('image_path', ''),
                        seo_title=row.get('seo_title', ''),
                        seo_description=row.get('seo_description', ''),
                        h1=row.get('h1', ''),
                        seo_text_html=row.get('seo_text_html', ''),
                        sort_order=int(row.get('sort_order', 0) or 0),
                        is_active=row.get('is_active', '1').lower() in ['1', 'true', 'yes']
                    )
                    db.session.add(pl)
                
                results['success'] += 1
            except Exception as e:
                results['errors'].append(f"Строка {row_num}: {str(e)}")
        
        db.session.commit()
    except Exception as e:
        results['errors'].append(f"Ошибка парсинга CSV: {str(e)}")
    
    return results


def import_size_items_csv(file_content):
    results = {'success': 0, 'errors': []}
    
    try:
        stream = io.StringIO(decode_csv_content(file_content))
        reader = csv.DictReader(stream, delimiter=';')
        
        for row_num, row in enumerate(reader, 2):
            try:
                category_slug = row.get('category_slug', '').strip()
                product_slug = row.get('product_slug', '').strip()
                size_text = row.get('size_text', '').strip()
                size_slug = row.get('size_slug', '').strip()
                
                if not size_slug and size_text:
                    size_slug = size_text.replace('/', '_').replace(' ', '_')
                
                if not category_slug or not product_slug or not size_text or not size_slug:
                    results['errors'].append(f"Строка {row_num}: пустые обязательные поля")
                    continue
                
                category = Category.query.filter_by(slug=category_slug).first()
                if not category:
                    results['errors'].append(f"Строка {row_num}: категория {category_slug} не найдена")
                    continue
                
                product_line = ProductLine.query.filter_by(category_id=category.id, slug=product_slug).first()
                if not product_line:
                    results['errors'].append(f"Строка {row_num}: линейка {product_slug} не найдена")
                    continue
                
                price_str = row.get('price', '0').strip().replace(',', '.')
                try:
                    price = float(price_str) if price_str else 0.0
                except:
                    price = 0.0
                
                existing = SizeItem.query.filter_by(product_line_id=product_line.id, size_slug=size_slug).first()
                if existing:
                    existing.size_text = size_text
                    existing.full_name = f"{product_line.name} {size_text}"
                    existing.sku = row.get('sku', '')
                    existing.price = price
                    existing.currency = row.get('currency', 'RUB')
                    existing.unit = row.get('unit', 'шт')
                    existing.in_stock = row.get('in_stock', '1').lower() in ['1', 'true', 'yes']
                    existing.image_path = row.get('image_path', '')
                    existing.pipe_dxs = row.get('pipe_dxs', '')
                    existing.pressure = row.get('pressure', '')
                    existing.mass_per_m = row.get('mass_per_m', '')
                    existing.min_bend_radius = row.get('min_bend_radius', '')
                    existing.max_len_coil = row.get('max_len_coil', '')
                    existing.max_len_drum = row.get('max_len_drum', '')
                else:
                    si = SizeItem(
                        product_line_id=product_line.id,
                        size_text=size_text,
                        size_slug=size_slug,
                        full_name=f"{product_line.name} {size_text}",
                        sku=row.get('sku', ''),
                        price=price,
                        currency=row.get('currency', 'RUB'),
                        unit=row.get('unit', 'шт'),
                        in_stock=row.get('in_stock', '1').lower() in ['1', 'true', 'yes'],
                        image_path=row.get('image_path', ''),
                        pipe_dxs = row.get('pipe_dxs', ''),
                        pressure = row.get('pressure', ''),
                        mass_per_m = row.get('mass_per_m', ''),
                        min_bend_radius = row.get('min_bend_radius', ''),
                        max_len_coil = row.get('max_len_coil', ''),
                        max_len_drum = row.get('max_len_drum', '')
                    )
                    db.session.add(si)
                
                results['success'] += 1
            except Exception as e:
                results['errors'].append(f"Строка {row_num}: {str(e)}")
        
        db.session.commit()
    except Exception as e:
        results['errors'].append(f"Ошибка парсинга CSV: {str(e)}")
    
    return results


def import_news_csv(file_content):
    results = {'success': 0, 'errors': []}
    
    try:
        stream = io.StringIO(decode_csv_content(file_content))
        reader = csv.DictReader(stream, delimiter=';')
        
        existing_slugs = [n.slug for n in News.query.all()]
        
        for row_num, row in enumerate(reader, 2):
            try:
                content = row.get('content', '').strip()
                date_str = row.get('date', '').strip()
                title = row.get('title', '').strip()
                slug = row.get('slug', '').strip()
                
                if not content:
                    results['errors'].append(f"Строка {row_num}: пустой контент")
                    continue
                
                if not title:
                    title = content[:50] + '...' if len(content) > 50 else content
                
                if not slug:
                    slug = generate_slug(title)
                    slug = make_unique_slug(slug, existing_slugs)
                
                try:
                    if date_str:
                        date = datetime.strptime(date_str, '%d.%m.%Y').date()
                    else:
                        date = datetime.utcnow().date()
                except:
                    date = datetime.utcnow().date()
                
                existing = News.query.filter_by(slug=slug).first()
                if existing:
                    existing.title = title
                    existing.date = date
                    existing.content_html = content
                    existing.seo_title = row.get('seo_title', '')
                    existing.seo_description = row.get('seo_description', '')
                    existing.h1 = row.get('h1', '')
                    existing.is_published = row.get('is_published', '1').lower() in ['1', 'true', 'yes']
                else:
                    news = News(
                        title=title,
                        slug=slug,
                        date=date,
                        content_html=content,
                        seo_title=row.get('seo_title', ''),
                        seo_description=row.get('seo_description', ''),
                        h1=row.get('h1', ''),
                        is_published=row.get('is_published', '1').lower() in ['1', 'true', 'yes']
                    )
                    db.session.add(news)
                    existing_slugs.append(slug)
                
                results['success'] += 1
            except Exception as e:
                results['errors'].append(f"Строка {row_num}: {str(e)}")
        
        db.session.commit()
    except Exception as e:
        results['errors'].append(f"Ошибка парсинга CSV: {str(e)}")
    
    return results
