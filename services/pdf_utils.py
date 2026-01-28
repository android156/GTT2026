import os
from pypdf import PdfReader, PdfWriter


def get_pdf_metadata(file_path):
    """Get PDF metadata."""
    if not file_path:
        return None
    
    full_path = file_path.lstrip('/')
    if not os.path.exists(full_path):
        return None
    
    try:
        reader = PdfReader(full_path)
        metadata = reader.metadata
        
        return {
            'title': metadata.get('/Title', '') if metadata else '',
            'author': metadata.get('/Author', '') if metadata else '',
            'subject': metadata.get('/Subject', '') if metadata else '',
            'keywords': metadata.get('/Keywords', '') if metadata else '',
            'creator': metadata.get('/Creator', '') if metadata else '',
            'producer': metadata.get('/Producer', '') if metadata else '',
        }
    except Exception as e:
        return {'error': str(e)}


def update_pdf_metadata(file_path, title=None, author=None, subject=None, keywords=None):
    """Update PDF metadata and save the file."""
    if not file_path:
        return False, "No file path provided"
    
    full_path = file_path.lstrip('/')
    if not os.path.exists(full_path):
        return False, "File not found"
    
    try:
        reader = PdfReader(full_path)
        writer = PdfWriter()
        
        for page in reader.pages:
            writer.add_page(page)
        
        metadata = {}
        if title is not None:
            metadata['/Title'] = title
        if author is not None:
            metadata['/Author'] = author
        if subject is not None:
            metadata['/Subject'] = subject
        if keywords is not None:
            metadata['/Keywords'] = keywords
        
        if metadata:
            writer.add_metadata(metadata)
        
        temp_path = full_path + '.tmp'
        with open(temp_path, 'wb') as f:
            writer.write(f)
        
        os.replace(temp_path, full_path)
        
        return True, None
    except Exception as e:
        if os.path.exists(full_path + '.tmp'):
            try:
                os.remove(full_path + '.tmp')
            except:
                pass
        return False, str(e)


def rename_file(file_path, new_name):
    """Rename a file while preserving extension."""
    if not file_path or not new_name:
        return None, "Invalid parameters"
    
    full_path = file_path.lstrip('/')
    if not os.path.exists(full_path):
        return None, "File not found"
    
    try:
        from werkzeug.utils import secure_filename
        
        directory = os.path.dirname(full_path)
        old_filename = os.path.basename(full_path)
        _, ext = os.path.splitext(old_filename)
        
        safe_name = secure_filename(new_name)
        if not safe_name:
            return None, "Invalid filename"
        
        if not safe_name.lower().endswith(ext.lower()):
            new_filename = f"{safe_name}{ext}"
        else:
            new_filename = safe_name
        
        new_path = os.path.join(directory, new_filename)
        
        if os.path.exists(new_path) and new_path != full_path:
            return None, "File with this name already exists"
        
        os.rename(full_path, new_path)
        return '/' + new_path, None
    except Exception as e:
        return None, str(e)
