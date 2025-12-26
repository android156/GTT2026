\# INSTR 10: Импорт CSV и URL-инвентаризация



\## CSV импорт

Поддержать загрузку CSV в админке для:

\- Categories

\- ProductLines

\- SizeItems

\- News

\- Pages (опционально)



\## Шаблоны CSV (минимум)

\- categories.csv: name, slug, description\_html, image\_path, seo\_title, seo\_description, h1, seo\_text\_html, sort\_order, is\_active

\- product\_lines.csv: category\_slug, name, slug, description\_html, image\_path, seo\_title, seo\_description, h1, seo\_text\_html, sort\_order, is\_active

\- size\_items.csv: category\_slug, product\_slug, size\_text, size\_slug, sku, price, currency, unit, in\_stock, image\_path

\- news.csv: date, title, slug, content\_html, seo\_title, seo\_description, h1, seo\_text\_html



\## URL-инвентаризация

В репозитории хранить файл url\_inventory.csv (можно ваш экспорт из site-analyzer).

Скрипт проверки (например tools/check\_urls.py):

\- читает url\_inventory.csv

\- для URL вида /catalog/... проверяет:

&nbsp; - 301 на новый URL

&nbsp; - новый URL отдаёт 200



