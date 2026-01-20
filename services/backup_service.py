import json
from datetime import datetime, date
from extensions import db
from models import (
    User, Page, MenuItem, Category, ProductLine, SizeItem, News, DocumentFile,
    Lead, Service, ServiceImage, HomeGalleryImage, RedirectRule, Setting,
    SiteSection, ProductLineImage, AccessoryBlock
)


def serialize_value(value):
    """Convert value to JSON-serializable format."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def model_to_dict(obj, exclude_fields=None):
    """Convert SQLAlchemy model instance to dictionary."""
    if exclude_fields is None:
        exclude_fields = []
    
    result = {}
    for column in obj.__table__.columns:
        if column.name not in exclude_fields:
            result[column.name] = serialize_value(getattr(obj, column.name))
    return result


def export_database():
    """Export all database tables to JSON format."""
    backup_data = {
        'version': '1.0',
        'exported_at': datetime.utcnow().isoformat(),
        'tables': {}
    }
    
    backup_data['tables']['users'] = [model_to_dict(u) for u in User.query.all()]
    backup_data['tables']['pages'] = [model_to_dict(p) for p in Page.query.all()]
    backup_data['tables']['menu_items'] = [model_to_dict(m) for m in MenuItem.query.all()]
    backup_data['tables']['categories'] = [model_to_dict(c) for c in Category.query.all()]
    backup_data['tables']['product_lines'] = [model_to_dict(pl) for pl in ProductLine.query.all()]
    backup_data['tables']['product_line_images'] = [model_to_dict(pli) for pli in ProductLineImage.query.all()]
    backup_data['tables']['size_items'] = [model_to_dict(si) for si in SizeItem.query.all()]
    backup_data['tables']['news'] = [model_to_dict(n) for n in News.query.all()]
    backup_data['tables']['document_files'] = [model_to_dict(d) for d in DocumentFile.query.all()]
    backup_data['tables']['leads'] = [model_to_dict(l) for l in Lead.query.all()]
    backup_data['tables']['services'] = [model_to_dict(s) for s in Service.query.all()]
    backup_data['tables']['service_images'] = [model_to_dict(si) for si in ServiceImage.query.all()]
    backup_data['tables']['home_gallery_images'] = [model_to_dict(hg) for hg in HomeGalleryImage.query.all()]
    backup_data['tables']['redirect_rules'] = [model_to_dict(r) for r in RedirectRule.query.all()]
    backup_data['tables']['settings'] = [model_to_dict(s) for s in Setting.query.all()]
    backup_data['tables']['site_sections'] = [model_to_dict(ss) for ss in SiteSection.query.all()]
    backup_data['tables']['accessory_blocks'] = [model_to_dict(ab) for ab in AccessoryBlock.query.all()]
    
    return json.dumps(backup_data, ensure_ascii=False, indent=2)


def parse_datetime(value):
    """Parse ISO datetime string to datetime object."""
    if not value:
        return None
    try:
        if 'T' in value:
            return datetime.fromisoformat(value.replace('Z', '+00:00').replace('+00:00', ''))
        return datetime.strptime(value, '%Y-%m-%d')
    except (ValueError, TypeError):
        return None


def parse_date(value):
    """Parse ISO date string to date object."""
    if not value:
        return None
    try:
        if 'T' in value:
            return datetime.fromisoformat(value.replace('Z', '+00:00').replace('+00:00', '')).date()
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def import_table(model_class, records, date_fields=None, datetime_fields=None):
    """Import records into a table, updating existing or creating new."""
    if date_fields is None:
        date_fields = []
    if datetime_fields is None:
        datetime_fields = []
    
    imported = 0
    updated = 0
    
    for record in records:
        record_id = record.get('id')
        
        for field in date_fields:
            if field in record:
                record[field] = parse_date(record[field])
        
        for field in datetime_fields:
            if field in record:
                record[field] = parse_datetime(record[field])
        
        existing = model_class.query.get(record_id) if record_id else None
        
        if existing:
            for key, value in record.items():
                if key != 'id' and hasattr(existing, key):
                    setattr(existing, key, value)
            updated += 1
        else:
            new_record = model_class(**record)
            db.session.add(new_record)
            imported += 1
    
    return imported, updated


def import_database(json_data, clear_existing=False):
    """Import database from JSON format."""
    try:
        backup_data = json.loads(json_data)
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON format: {str(e)}"
    
    if 'tables' not in backup_data:
        return False, "Invalid backup format: 'tables' key not found"
    
    tables = backup_data['tables']
    results = {}
    
    try:
        if clear_existing:
            AccessoryBlock.query.delete()
            ProductLineImage.query.delete()
            ServiceImage.query.delete()
            HomeGalleryImage.query.delete()
            SizeItem.query.delete()
            ProductLine.query.delete()
            Category.query.delete()
            Service.query.delete()
            Page.query.delete()
            MenuItem.query.delete()
            News.query.delete()
            DocumentFile.query.delete()
            Lead.query.delete()
            RedirectRule.query.delete()
            Setting.query.delete()
            SiteSection.query.delete()
            db.session.commit()
        
        if 'users' in tables:
            imported, updated = import_table(User, tables['users'])
            results['users'] = {'imported': imported, 'updated': updated}
        
        if 'settings' in tables:
            imported, updated = import_table(Setting, tables['settings'])
            results['settings'] = {'imported': imported, 'updated': updated}
        
        if 'site_sections' in tables:
            imported, updated = import_table(SiteSection, tables['site_sections'], datetime_fields=['updated_at'])
            results['site_sections'] = {'imported': imported, 'updated': updated}
        
        if 'pages' in tables:
            imported, updated = import_table(Page, tables['pages'], datetime_fields=['updated_at'])
            results['pages'] = {'imported': imported, 'updated': updated}
        
        if 'menu_items' in tables:
            imported, updated = import_table(MenuItem, tables['menu_items'])
            results['menu_items'] = {'imported': imported, 'updated': updated}
        
        if 'categories' in tables:
            imported, updated = import_table(Category, tables['categories'])
            results['categories'] = {'imported': imported, 'updated': updated}
        
        if 'product_lines' in tables:
            imported, updated = import_table(ProductLine, tables['product_lines'], datetime_fields=['updated_at'])
            results['product_lines'] = {'imported': imported, 'updated': updated}
        
        if 'product_line_images' in tables:
            imported, updated = import_table(ProductLineImage, tables['product_line_images'], datetime_fields=['created_at'])
            results['product_line_images'] = {'imported': imported, 'updated': updated}
        
        if 'size_items' in tables:
            imported, updated = import_table(SizeItem, tables['size_items'], datetime_fields=['updated_at'])
            results['size_items'] = {'imported': imported, 'updated': updated}
        
        if 'services' in tables:
            imported, updated = import_table(Service, tables['services'], datetime_fields=['updated_at'])
            results['services'] = {'imported': imported, 'updated': updated}
        
        if 'service_images' in tables:
            imported, updated = import_table(ServiceImage, tables['service_images'], datetime_fields=['created_at'])
            results['service_images'] = {'imported': imported, 'updated': updated}
        
        if 'home_gallery_images' in tables:
            imported, updated = import_table(HomeGalleryImage, tables['home_gallery_images'], datetime_fields=['created_at'])
            results['home_gallery_images'] = {'imported': imported, 'updated': updated}
        
        if 'accessory_blocks' in tables:
            imported, updated = import_table(AccessoryBlock, tables['accessory_blocks'], datetime_fields=['created_at'])
            results['accessory_blocks'] = {'imported': imported, 'updated': updated}
        
        if 'news' in tables:
            imported, updated = import_table(News, tables['news'], date_fields=['date'], datetime_fields=['created_at'])
            results['news'] = {'imported': imported, 'updated': updated}
        
        if 'document_files' in tables:
            imported, updated = import_table(DocumentFile, tables['document_files'], datetime_fields=['created_at'])
            results['document_files'] = {'imported': imported, 'updated': updated}
        
        if 'leads' in tables:
            imported, updated = import_table(Lead, tables['leads'], datetime_fields=['created_at'])
            results['leads'] = {'imported': imported, 'updated': updated}
        
        if 'redirect_rules' in tables:
            imported, updated = import_table(RedirectRule, tables['redirect_rules'], datetime_fields=['created_at', 'updated_at'])
            results['redirect_rules'] = {'imported': imported, 'updated': updated}
        
        db.session.commit()
        
        return True, results
    
    except Exception as e:
        db.session.rollback()
        return False, f"Import error: {str(e)}"
