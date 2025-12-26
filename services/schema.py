import json
from flask import request
from services.seo import get_absolute_url


def generate_product_jsonld(size_item, product_line, category):
    availability = "https://schema.org/InStock" if size_item.in_stock else "https://schema.org/OutOfStock"
    
    url = get_absolute_url(f"/{category.slug}/{product_line.slug}/{size_item.size_slug}/")
    
    image = size_item.image_path or product_line.image_path or category.image_path
    if image and not image.startswith('http'):
        image = get_absolute_url(image)
    
    schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": size_item.full_name or f"{product_line.name} {size_item.size_text}",
        "sku": size_item.sku or "",
        "brand": {
            "@type": "Brand",
            "name": category.name
        },
        "description": f"{product_line.name} размер {size_item.size_text}",
        "offers": {
            "@type": "Offer",
            "url": url,
            "priceCurrency": size_item.currency or "RUB",
            "price": str(size_item.price) if size_item.price else "0",
            "availability": availability,
            "seller": {
                "@type": "Organization",
                "name": "ГлавТрубТорг"
            }
        }
    }
    
    if image:
        schema["image"] = image
    
    return json.dumps(schema, ensure_ascii=False, indent=2)


def generate_breadcrumb_jsonld(breadcrumbs):
    items = []
    for i, crumb in enumerate(breadcrumbs, 1):
        item = {
            "@type": "ListItem",
            "position": i,
            "name": crumb['name']
        }
        if crumb.get('url'):
            item["item"] = get_absolute_url(crumb['url'])
        items.append(item)
    
    schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items
    }
    
    return json.dumps(schema, ensure_ascii=False, indent=2)


def generate_organization_jsonld():
    schema = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "ГлавТрубТорг",
        "url": get_absolute_url("/"),
        "description": "Продажа труб, изоляционных материалов и комплектующих",
        "contactPoint": {
            "@type": "ContactPoint",
            "contactType": "sales",
            "availableLanguage": "Russian"
        }
    }
    
    return json.dumps(schema, ensure_ascii=False, indent=2)
