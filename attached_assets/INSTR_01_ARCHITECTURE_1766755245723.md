\# INSTR 01: Архитектура проекта



\## Цель

Сделать модульный Flask-проект (public + admin + services).



\## Требуемая структура (минимум)

\- app.py (точка входа)

\- config.py

\- extensions.py (db, migrate, login\_manager, csrf)

\- models.py (или пакет models/)

\- blueprints/

&nbsp; - public.py (публичные маршруты)

&nbsp; - admin.py (админка)

&nbsp; - redirects.py (middleware/хук редиректов)

\- services/

&nbsp; - seo.py (meta + canonical + og)

&nbsp; - schema.py (JSON-LD генерация)

&nbsp; - slug.py (валидация slug + reserved)

&nbsp; - importers.py (CSV импорт)

\- templates/

&nbsp; - base.html

&nbsp; - public/\*

&nbsp; - admin/\*

\- static/

&nbsp; - css/variables.css, main.css

&nbsp; - img/...

\- migrations/ (alembic)



\## Стандарты

\- Использовать Flask Blueprint.

\- Использовать Flask-Login для админки.

\- Использовать Flask-WTF + CSRF.

\- Ошибки: кастомные 404/500.

\- Логи: базовые request logs.



\## Конфиг

\- ENV: FLASK\_ENV, SECRET\_KEY, ADMIN\_USERNAME, ADMIN\_PASSWORD (или первичная инициализация), TELEGRAM\_TOKEN, TELEGRAM\_CHAT\_ID.

\- SQLite по умолчанию, возможность переключить на PostgreSQL по DATABASE\_URL.



