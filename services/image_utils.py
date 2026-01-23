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
            
            if img.mode in ('RGBA', 'P'):
                if convert_to_webp:
                    white_bg = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    white_bg.paste(img, mask=img.split()[3])
                    img = white_bg
                else:
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


def apply_watermark(image_path, watermark_path, opacity=0.4, scale=0.15):
    """
    Apply soft watermark pattern - one watermark per row at random position.
    
    Args:
        image_path: Path to the original image
        watermark_path: Path to the watermark image (PNG with transparency recommended)
        opacity: Opacity of the watermark (0.0 - 1.0)
        scale: Scale factor for watermark relative to image width (0.1 - 0.5)
    
    Returns:
        PIL Image object with watermark applied, or None on error
    """
    import random
    import hashlib
    
    if not image_path or not watermark_path:
        return None
    
    img_full_path = image_path.lstrip('/')
    wm_full_path = watermark_path.lstrip('/')
    
    if not os.path.exists(img_full_path) or not os.path.exists(wm_full_path):
        return None
    
    try:
        base_image = Image.open(img_full_path)
        watermark = Image.open(wm_full_path)
        
        if base_image.mode != 'RGBA':
            base_image = base_image.convert('RGBA')
        if watermark.mode != 'RGBA':
            watermark = watermark.convert('RGBA')
        
        img_width, img_height = base_image.size
        wm_width, wm_height = watermark.size
        
        target_width = int(img_width * scale)
        if target_width < 50:
            target_width = 50
        ratio = target_width / wm_width
        target_height = int(wm_height * ratio)
        watermark = watermark.resize((target_width, target_height), Image.LANCZOS)
        wm_width, wm_height = watermark.size
        
        if opacity < 1.0:
            alpha = watermark.split()[3]
            alpha = alpha.point(lambda p: int(p * opacity))
            watermark.putalpha(alpha)
        
        transparent_layer = Image.new('RGBA', base_image.size, (0, 0, 0, 0))
        
        seed = int(hashlib.md5(image_path.encode()).hexdigest()[:8], 16)
        random.seed(seed)
        
        spacing_y = int(wm_height * 2.5)
        
        y = wm_height // 2
        while y < img_height - wm_height // 2:
            max_x = img_width - wm_width
            if max_x > 0:
                x = random.randint(0, max_x)
            else:
                x = 0
            transparent_layer.paste(watermark, (x, y), watermark)
            y += spacing_y
        
        result = Image.alpha_composite(base_image, transparent_layer)
        
        return result
    except Exception:
        return None


def get_watermarked_image_bytes(image_path, watermark_path, output_format='JPEG', opacity=1.0):
    """
    Get watermarked image as bytes for serving via Flask.
    
    Args:
        image_path: Path to the original image
        watermark_path: Path to the watermark image
        output_format: Output format ('JPEG', 'PNG', 'WEBP')
        opacity: Opacity of the watermark (0.1 - 1.0)
    
    Returns:
        Tuple of (bytes, content_type) or (None, None) on error
    """
    import io
    
    result = apply_watermark(image_path, watermark_path, opacity=opacity)
    if result is None:
        return None, None
    
    try:
        output = io.BytesIO()
        
        if output_format.upper() == 'JPEG':
            if result.mode == 'RGBA':
                result = result.convert('RGB')
            result.save(output, 'JPEG', quality=90, optimize=True)
            content_type = 'image/jpeg'
        elif output_format.upper() == 'PNG':
            result.save(output, 'PNG', optimize=True)
            content_type = 'image/png'
        elif output_format.upper() == 'WEBP':
            result.save(output, 'WEBP', quality=90, optimize=True)
            content_type = 'image/webp'
        else:
            if result.mode == 'RGBA':
                result = result.convert('RGB')
            result.save(output, 'JPEG', quality=90)
            content_type = 'image/jpeg'
        
        output.seek(0)
        return output.getvalue(), content_type
    except Exception:
        return None, None
