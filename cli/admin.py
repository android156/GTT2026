import os
import sys
import logging
import click
from flask import current_app
from flask.cli import AppGroup

logger = logging.getLogger(__name__)

admin_cli = AppGroup('admin', help='Admin user management commands')


@admin_cli.command('ensure')
@click.option('--reset-password', is_flag=True, help='Force reset admin password')
def ensure_admin(reset_password):
    """
    Ensure admin user exists. Creates if not found.
    Use --reset-password to force password update.
    """
    from extensions import db
    from models import User
    
    username = os.environ.get('ADMIN_USERNAME')
    password = os.environ.get('ADMIN_PASSWORD')
    
    if not username:
        msg = 'ADMIN_USERNAME environment variable is not set'
        logger.error(msg)
        click.echo(f'ERROR: {msg}', err=True)
        sys.exit(1)
    
    if not password:
        msg = 'ADMIN_PASSWORD environment variable is not set'
        logger.error(msg)
        click.echo(f'ERROR: {msg}', err=True)
        sys.exit(1)
    
    admin = User.query.filter_by(username=username).first()
    
    if admin is None:
        admin = User(
            username=username,
            role='admin',
            is_active=True
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        msg = f'Admin user created: {username}'
        logger.info(msg)
        click.echo(msg)
    else:
        if reset_password:
            admin.set_password(password)
            db.session.commit()
            msg = f'Admin password reset for user: {username}'
            logger.info(msg)
            click.echo(msg)
        else:
            msg = f'Admin user exists: {username} (no changes)'
            logger.info(msg)
            click.echo(msg)


@admin_cli.command('info')
def admin_info():
    """
    Show admin user status (without passwords).
    """
    from models import User
    
    username = os.environ.get('ADMIN_USERNAME', 'admin')
    
    admin = User.query.filter_by(username=username).first()
    
    if admin:
        click.echo(f'Admin user "{username}" exists')
        click.echo(f'  Role: {admin.role}')
        click.echo(f'  Active: {admin.is_active}')
    else:
        click.echo(f'Admin user "{username}" does not exist')
        click.echo('Run "flask admin ensure" to create')
