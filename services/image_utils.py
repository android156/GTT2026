import os
from PIL import Image
from werkzeug.utils import secure_filename


def get_image_info(image_path):
    """Get image file size and dimensions."""
    if not image_path:
        return None
    
    full_path = image_path.lstrip('/')
    if not os.path.exists(full_path):
        return None
    
    try:
        file_size = os.path.getsize(full_path)
        with Image.open(full_path) as img:
            width, height = img.size
            format_name = img.format or 'Unknown'
        
        if file_size < 1024:
            size_str = f"{file_size} B"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size / (1024 * 1024):.2f} MB"
        
        return {
            'file_size': file_size,
            'file_size_str': size_str,
            'width': width,
            'height': height,
            'dimensions': f"{width}x{height}",
            'format': format_name
        }
    except Exception:
        return None


def optimize_image(image_path, quality=85, max_width=1920, max_height=1920, convert_to_webp=False):
    """Optimize image: resize if needed and compress."""
    if not image_path:
        return None, "No image path provided"
    
    full_path = image_path.lstrip('/')
    if not os.path.exists(full_path):
        return None, "File not found"
    
    try:
        with Image.open(full_path) as img:
            original_format = img.format
            
            if img.mode in ('RGBA', 'P') and not convert_to_webp:
                img = img.convert('RGBA')
            else:
                img = img.convert('RGB')
            
            width, height = img.size
            if width > max_width or height > max_height:
                ratio = min(max_width / width, max_height / height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                img = img.resize((new_width, new_height), Image.LANCZOS)
            
            directory = os.path.dirname(full_path)
            filename = os.path.basename(full_path)
            name, ext = os.path.splitext(filename)
            
            if convert_to_webp:
                new_filename = f"{name}.webp"
                new_path = os.path.join(directory, new_filename)
                img.save(new_path, 'WEBP', quality=quality, optimize=True)
            else:
                new_filename = filename
                new_path = full_path
                if ext.lower() in ('.jpg', '.jpeg'):
                    img.save(new_path, 'JPEG', quality=quality, optimize=True)
                elif ext.lower() == '.png':
                    img.save(new_path, 'PNG', optimize=True)
                elif ext.lower() == '.webp':
                    img.save(new_path, 'WEBP', quality=quality, optimize=True)
                else:
                    img.save(new_path, quality=quality)
            
            return '/' + new_path, None
    except Exception as e:
        return None, str(e)


def rename_image_file(image_path, new_name):
    """Rename image file while preserving extension."""
    if not image_path or not new_name:
        return None, "Invalid parameters"
    
    full_path = image_path.lstrip('/')
    if not os.path.exists(full_path):
        return None, "File not found"
    
    try:
        directory = os.path.dirname(full_path)
        old_filename = os.path.basename(full_path)
        _, ext = os.path.splitext(old_filename)
        
        safe_name = secure_filename(new_name)
        if not safe_name:
            return None, "Invalid filename"
        
        new_filename = f"{safe_name}{ext}"
        new_path = os.path.join(directory, new_filename)
        
        if os.path.exists(new_path) and new_path != full_path:
            return None, "File with this name already exists"
        
        os.rename(full_path, new_path)
        return '/' + new_path, None
    except Exception as e:
        return None, str(e)
