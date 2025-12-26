from flask import Blueprint, request, redirect
from models import RedirectRule
import re

redirects_bp = Blueprint('redirects', __name__)


def check_redirects(app):
    @app.before_request
    def handle_redirects():
        path = request.path
        
        if path.startswith('/static/') or path.startswith('/admin/static/'):
            return None
        
        db_rule = RedirectRule.query.filter_by(from_path=path, is_active=True).first()
        if db_rule:
            return redirect(db_rule.to_path, code=db_rule.code)
        
        path_with_slash = path if path.endswith('/') else path + '/'
        if path != path_with_slash:
            db_rule_slash = RedirectRule.query.filter_by(from_path=path_with_slash, is_active=True).first()
            if db_rule_slash:
                return redirect(db_rule_slash.to_path, code=db_rule_slash.code)
        
        catalog_match = re.match(r'^/catalog(/.*)?$', path)
        if catalog_match and path != '/catalog/' and path != '/catalog':
            rest = catalog_match.group(1) or ''
            if rest:
                new_path = rest if rest.endswith('/') else rest + '/'
                return redirect(new_path, code=301)
        
        if path != '/' and not path.endswith('/') and '.' not in path.split('/')[-1]:
            return redirect(path + '/', code=301)
        
        return None
