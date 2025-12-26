\# INSTR 03: Роутинг и URL без конфликтов



\## Зарезервированные пути (нельзя использовать как category\_slug)

about, catalog, services, price, documentation, contacts, news, static, admin, login, logout, sitemap.xml, robots.txt



\## Публичные маршруты

\- / (главная)

\- /about/ /services/ /price/ /documentation/ /contacts/ (из таблицы Page по url\_path)

\- /catalog/ (лист категорий)

\- /news/ и /news/<slug>/

\- Динамический каталог:

&nbsp; - /<category\_slug>/

&nbsp; - /<category\_slug>/<product\_slug>/

&nbsp; - /<category\_slug>/<product\_slug>/<size\_slug>/



\## Правило разрешения конфликтов

1\) Сначала match фиксированных путей (about/news/etc).

2\) Потом match /catalog/ и /news/.

3\) Потом match динамического каталога в корне.

4\) Если category\_slug входит в reserved — 404.



\## Завершающий слеш

Все страницы должны быть доступны только со слешем в конце.

Запрос без слеша -> 301 на вариант со слешем.



