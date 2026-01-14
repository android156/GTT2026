# ГлавТрубТорг - Flask Website

## Обзор
Корпоративный сайт компании ГлавТрубТорг с 4-уровневым каталогом продукции, админкой, SEO-оптимизацией и Telegram-ботом.

## Текущее состояние
- Полностью рабочий Flask-сайт
- PostgreSQL база данных
- 4-уровневый каталог: Каталог -> Категория -> Линейка -> Типоразмер
- Админка с полным CRUD для всех сущностей
- SEO: meta, canonical, OpenGraph, JSON-LD, sitemap.xml, robots.txt
- Редиректы: системные (/catalog/ -> /) и ручные из БД
- Telegram-бот (MVP)
- CSV импорт для категорий, линеек, типоразмеров, новостей

## Технологии
- Python 3.11, Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF
- PostgreSQL (через DATABASE_URL)
- Jinja2 шаблоны
- CSS без фреймворков

## Структура проекта
```
├── app.py              # Точка входа
├── config.py           # Конфигурация
├── extensions.py       # Flask расширения
├── models.py           # Модели БД
├── blueprints/
│   ├── public.py       # Публичные маршруты
│   ├── admin.py        # Админка
│   └── redirects.py    # Редиректы
├── services/
│   ├── seo.py          # SEO сервисы
│   ├── schema.py       # JSON-LD
│   ├── slug.py         # Слаги
│   └── importers.py    # CSV импорт
├── templates/
│   ├── base.html
│   ├── public/
│   └── admin/
├── static/css/
└── telegram_bot.py
```

## Запуск
```bash
python app.py
```

## Админка
- URL: /admin/
- Логин: admin / admin123

## Ключевые URL
- `/` - Главная
- `/catalog/` - Каталог (уровень 1)
- `/<category>/` - Категория (уровень 2)
- `/<category>/<product>/` - Линейка (уровень 3)
- `/<category>/<product>/<size>/` - Типоразмер (уровень 4)
- `/news/` - Новости
- `/admin/` - Админка

## Редиректы
- `/catalog/xxx/` -> `/xxx/` (301, автоматически)
- `/xxx` -> `/xxx/` (301, добавление слеша)
- Ручные редиректы через админку имеют приоритет

## Последние изменения
- 2026-01-14: Добавлена функция поворота изображений галереи на 90° (влево/вправо) в админке
- 2025-12-29: Реструктуризация админки - группировка меню (Контент, Каталог, Услуги, Заявки, Настройки)
- 2025-12-29: Добавлена модель SiteSection для управления разделами сайта (главная, новости, каталог, услуги)
- 2025-12-29: Перенос Hero-настроек из MenuItem в соответствующие модели (Page, Category, Service, SiteSection)
- 2025-12-29: Добавлена Яндекс.Карта на страницу контактов (/contacts/)
- 2025-12-26: Создан проект с нуля по ТЗ

## Модели БД
- **User** - пользователи админки
- **Page** - статические страницы (about, contacts, price, documentation) + hero_image/title/subtitle
- **MenuItem** - пункты меню
- **Category** - категории каталога + hero_image/title/subtitle
- **ProductLine** - линейки продукции
- **SizeItem** - типоразмеры
- **Service** - услуги + hero_image/title/subtitle
- **News** - новости
- **SiteSection** - разделы сайта (index, news, catalog, services) с hero и SEO настройками
- **Lead** - заявки
- **RedirectRule** - редиректы
- **Setting** - общие настройки
- **DocumentFile** - документы
