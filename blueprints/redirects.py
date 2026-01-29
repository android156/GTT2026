from flask import Blueprint, request, redirect
from models import RedirectRule
import re

redirects_bp = Blueprint('redirects', __name__)


def match_pattern(pattern, path):
    """Match a pattern with * wildcard against a path.
    Returns the matched wildcard portion if matched, None otherwise.
    Example: pattern='/catalog/*', path='/catalog/abc/' returns 'abc/'
    """
    if '*' not in pattern:
        return None
    
    regex_pattern = '^' + re.escape(pattern).replace(r'\*', '(.*)') + '$'
    match = re.match(regex_pattern, path)
    if match:
        return match.group(1) if match.groups() else ''
    return None


def apply_pattern_redirect(from_pattern, to_pattern, path):
    """Apply pattern-based redirect.
    Replaces * in to_pattern with the matched portion from from_pattern.
    """
    matched = match_pattern(from_pattern, path)
    if matched is not None:
        result = to_pattern.replace('*', matched)
        if not result.endswith('/') and '.' not in result.split('/')[-1]:
            result += '/'
        return result
    return None


def check_redirects(app):
    @app.before_request
    def handle_redirects():
        path = request.path
        
        if path.startswith('/static/') or path.startswith('/admin/static/'):
            return None
        
        db_rule = RedirectRule.query.filter_by(from_path=path, is_active=True, is_pattern=False).first()
        if db_rule:
            return redirect(db_rule.to_path, code=db_rule.code)
        
        path_with_slash = path if path.endswith('/') else path + '/'
        if path != path_with_slash:
            db_rule_slash = RedirectRule.query.filter_by(from_path=path_with_slash, is_active=True, is_pattern=False).first()
            if db_rule_slash:
                return redirect(db_rule_slash.to_path, code=db_rule_slash.code)
        
        pattern_rules = RedirectRule.query.filter_by(is_active=True, is_pattern=True).all()
        for rule in pattern_rules:
            new_path = apply_pattern_redirect(rule.from_path, rule.to_path, path)
            if new_path:
                return redirect(new_path, code=rule.code)
            if path != path_with_slash:
                new_path = apply_pattern_redirect(rule.from_path, rule.to_path, path_with_slash)
                if new_path:
                    return redirect(new_path, code=rule.code)
        
        if path != '/' and not path.endswith('/') and '.' not in path.split('/')[-1]:
            return redirect(path + '/', code=301)
        
        return None
