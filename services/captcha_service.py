import random
import hashlib
import time
from flask import session

def generate_captcha():
    """Generate simple math captcha (addition/subtraction)."""
    a = random.randint(1, 20)
    b = random.randint(1, 20)
    
    if random.choice([True, False]):
        question = f"{a} + {b}"
        answer = a + b
    else:
        if a < b:
            a, b = b, a
        question = f"{a} - {b}"
        answer = a - b
    
    timestamp = int(time.time())
    token = hashlib.sha256(f"{answer}:{timestamp}:secret_salt_glavtrubtorg".encode()).hexdigest()[:16]
    
    session['captcha_answer'] = answer
    session['captcha_timestamp'] = timestamp
    session['captcha_token'] = token
    
    return {
        'question': question,
        'token': token
    }


def verify_captcha(user_answer, token):
    """Verify captcha answer."""
    if not user_answer or not token:
        return False
    
    stored_answer = session.get('captcha_answer')
    stored_token = session.get('captcha_token')
    stored_timestamp = session.get('captcha_timestamp')
    
    if not stored_answer or not stored_token:
        return False
    
    if token != stored_token:
        return False
    
    if stored_timestamp and (int(time.time()) - stored_timestamp > 600):
        return False
    
    try:
        if int(user_answer) == stored_answer:
            session.pop('captcha_answer', None)
            session.pop('captcha_token', None)
            session.pop('captcha_timestamp', None)
            return True
    except (ValueError, TypeError):
        pass
    
    return False


def check_honeypot(form_data, honeypot_field='website'):
    """Check if honeypot field is filled (bot detection)."""
    honeypot_value = form_data.get(honeypot_field, '')
    return len(honeypot_value) == 0
