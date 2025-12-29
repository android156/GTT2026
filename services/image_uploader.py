import os
import uuid
from PIL import Image
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_SIZE = (1920, 1080)
THUMB_SIZE = (400, 300)
QUALITY = 85


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def ensure_upload_dirs():
    dirs = [
        os.path.join(UPLOAD_FOLDER, 'categories'),
        os.path.join(UPLOAD_FOLDER, 'products'),
        os.path.join(UPLOAD_FOLDER, 'hero'),
        os.path.join(UPLOAD_FOLDER, 'news'),
        os.path.join(UPLOAD_FOLDER, 'misc'),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def generate_filename(original_filename):
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
    if ext == 'jpeg':
        ext = 'jpg'
    return f"{uuid.uuid4().hex[:12]}.{ext}"


def compress_image(image, max_size=MAX_SIZE, quality=QUALITY):
    if image.mode in ('RGBA', 'P'):
        image = image.convert('RGB')
    
    image.thumbnail(max_size, Image.Resampling.LANCZOS)
    return image


def save_uploaded_image(file, subfolder='misc', max_size=MAX_SIZE, quality=QUALITY):
    if not file or not file.filename:
        return None
    
    if not allowed_file(file.filename):
        return None
    
    ensure_upload_dirs()
    
    filename = generate_filename(file.filename)
    folder = os.path.join(UPLOAD_FOLDER, subfolder)
    os.makedirs(folder, exist_ok=True)
    
    filepath = os.path.join(folder, filename)
    
    try:
        image = Image.open(file)
        image = compress_image(image, max_size, quality)
        image.save(filepath, 'JPEG' if filename.endswith('.jpg') else image.format, quality=quality, optimize=True)
        return f"/{filepath}"
    except Exception as e:
        print(f"Image upload error: {e}")
        return None


def delete_image(image_path):
    if not image_path:
        return
    
    if image_path.startswith('/'):
        image_path = image_path[1:]
    
    if os.path.exists(image_path):
        try:
            os.remove(image_path)
        except Exception as e:
            print(f"Image delete error: {e}")
