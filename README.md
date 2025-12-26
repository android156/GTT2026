# ГлавТрубТорг - Flask Website

Сайт компании ГлавТрубТорг на Flask с 4-уровневым каталогом, админкой, SEO-оптимизацией и Telegram-ботом.

## Запуск

```bash
python app.py
```

Сайт будет доступен по адресу: http://localhost:5000

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
│   ├── schema.py       # JSON-LD микроразметка
│   ├── slug.py         # Работа со слагами
│   ├── importers.py    # CSV импорт
│   └── rag_service.py  # Заглушка RAG
├── templates/
│   ├── base.html
│   ├── public/         # Публичные шаблоны
│   └── admin/          # Шаблоны админки
├── static/
│   └── css/
├── telegram_bot.py     # Telegram бот (MVP)
└── tools/
    └── check_urls.py   # Проверка редиректов
```

## Админка

- URL: /admin/
- Логин по умолчанию: admin / admin123

### Разделы админки:
1. Страницы
2. Меню
3. Категории
4. Линейки продукции
5. Типоразмеры
6. Новости
7. Документы
8. Заявки (Leads)
9. Редиректы
10. Настройки

## URL-структура

### Публичные страницы:
- `/` - Главная
- `/about/` - О компании
- `/services/` - Услуги
- `/price/` - Цены
- `/documentation/` - Документация
- `/contacts/` - Контакты
- `/news/` - Новости
- `/catalog/` - Каталог (уровень 1)

### Каталог (4 уровня):
- `/<category_slug>/` - Категория
- `/<category_slug>/<product_slug>/` - Линейка
- `/<category_slug>/<product_slug>/<size_slug>/` - Типоразмер

### Редиректы:
Старые URL `/catalog/...` автоматически редиректят на новые `/<...>/` с кодом 301.

## Импорт CSV

Форматы CSV файлов:

### categories.csv
```
name,slug,description_html,image_path,seo_title,seo_description,h1,seo_text_html,sort_order,is_active
```

### product_lines.csv
```
category_slug,name,slug,description_html,image_path,seo_title,seo_description,h1,seo_text_html,sort_order,is_active
```

### size_items.csv
```
category_slug,product_slug,size_text,size_slug,sku,price,currency,unit,in_stock,image_path
```

### news.csv
```
date,title,slug,content_html,seo_title,seo_description,h1,seo_text_html
```

## Настройка редиректов

1. В админке: /admin/redirects/
2. Укажите from_path и to_path (оба должны начинаться с /)
3. Выберите код (301 или 302)
4. Ручные редиректы имеют приоритет над системными

## Telegram бот

Для запуска бота:

1. Установите переменные окружения:
   - `TELEGRAM_TOKEN` - токен бота от @BotFather
   - `TELEGRAM_CHAT_ID` - ID чата для уведомлений

2. Запустите:
```bash
python telegram_bot.py
```

## SEO

- Автоматическая генерация title и description
- Canonical URL на всех страницах
- OpenGraph теги
- JSON-LD микроразметка (Product, BreadcrumbList, Organization)
- sitemap.xml и robots.txt

## Переменные окружения

```
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///glavtrubtorg.db  # или PostgreSQL URL
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
TELEGRAM_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
SITE_URL=https://glavtrubtorg.ru
```

## Миграции

```bash
flask db init      # Инициализация (один раз)
flask db migrate   # Создание миграции
flask db upgrade   # Применение миграций
```
