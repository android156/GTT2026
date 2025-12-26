import re
from config import RESERVED_SLUGS


def validate_slug(slug):
    if not slug:
        return False, "Slug не может быть пустым"
    
    if not re.match(r'^[a-z0-9_-]+$', slug):
        return False, "Slug может содержать только латинские буквы, цифры, дефис и подчёркивание"
    
    return True, ""


def is_reserved_slug(slug):
    return slug.lower() in [s.lower() for s in RESERVED_SLUGS]


def generate_slug(text):
    text = text.lower().strip()
    
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        ' ': '_', '-': '_', '/': '_'
    }
    
    result = ''
    for char in text:
        if char in translit_map:
            result += translit_map[char]
        elif char.isalnum():
            result += char
        elif char in '_-':
            result += '_'
    
    result = re.sub(r'_+', '_', result)
    result = result.strip('_')
    
    return result


def make_unique_slug(base_slug, existing_slugs):
    if base_slug not in existing_slugs:
        return base_slug
    
    counter = 1
    while f"{base_slug}_{counter}" in existing_slugs:
        counter += 1
    
    return f"{base_slug}_{counter}"
