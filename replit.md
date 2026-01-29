# ГлавТрубТорг - Flask Website

## Overview
This project is a corporate Flask website for ГлавТрубТорг, featuring a 4-level product catalog, a comprehensive administration panel, advanced SEO optimization, and a Telegram bot integration. The website aims to provide a robust online presence for the company, showcasing its products and services with detailed information and lead generation capabilities.

## User Preferences
The user prefers iterative development and expects the agent to ask before making major changes. The agent should prioritize clear and concise communication.

## System Architecture
The application is built on Python 3.11 with Flask, using Flask-SQLAlchemy for database interactions and Jinja2 for templating. PostgreSQL is used as the primary database. The UI/UX is based on custom CSS without external frameworks.

**Key Features:**
- **4-Level Product Catalog:** Organizes products into Catalog -> Category -> Product Line -> Size Item.
- **Admin Panel:** Full CRUD (Create, Read, Update, Delete) operations for all entities, including categories, product lines, size items, news, services, redirects, and document management.
- **SEO Optimization:** Comprehensive meta tags, canonical URLs, OpenGraph, JSON-LD schema, sitemap.xml, and robots.txt. SEO fields are available for various content types, including document types and product lines.
- **Redirect Management:** Both exact and pattern-based redirects are managed via the admin panel, with system-level rules for catalog and trailing slashes.
- **Document Management System:** Allows uploading, categorizing, and managing various document types with dedicated pages, SEO fields, and PDF metadata editing.
- **Product Accessory Matching:** An intelligent system for parsing product sizes and suggesting compatible accessories, supporting complex size specifications.
- **Discount and Price Visibility System:** Configurable discounts and options to hide prices for product lines and individual size items, with cascading logic.
- **Image Management:** Features include image optimization (compression, resize, WebP conversion), watermarking, rotation, and editing of alt, title, and caption for SEO.
- **CSV Import/Export:** Functionality to import and export data for categories, product lines, size items, and news.
- **Contact Forms:** Implemented with mathematical CAPTCHA, honeypot fields, and UTM tracking for lead generation. Submissions are sent via email (Yandex SMTP) and Telegram notifications.
- **WYSIWYG Editor:** Integrated CKEditor 5 for rich text editing in various content areas.
- **CLI Tools:** For administrator management (creation, password reset, status check).

**Project Structure:**
The project is modular, with `blueprints` for public, admin, and redirect routes. `services` contain business logic for SEO, slug generation, importers, size matching, image processing, and PDF utilities. `models.py` defines the database schema.

## External Dependencies
- **PostgreSQL:** Primary database.
- **Telegram Bot API:** For sending notifications about new leads.
- **Yandex SMTP:** For sending email notifications from contact forms.
- **CKEditor 5 Classic (CDN):** WYSIWYG editor for content management.
- **PyPDF:** For managing PDF metadata.