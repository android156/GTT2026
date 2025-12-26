\# INSTR 04: Логика каталога и UI-ожидания



\## /catalog/

\- плитки категорий: картинка + название + короткий текст (по желанию)

\- ссылку ведём на /<category\_slug>/



\## /<category\_slug>/

\- H1

\- описание (description\_html)

\- список линеек (ProductLine) карточками/таблицей



\## /<category\_slug>/<product\_slug>/

\- H1

\- описание линейки

\- таблица типоразмеров (SizeItem): size\_text, price, in\_stock

\- size\_text кликабелен на уровень 4



\## /<category\_slug>/<product\_slug>/<size\_slug>/

\- карточка типоразмера:

&nbsp; - full\_name

&nbsp; - характеристики (минимум: sku, availability, unit, price)

&nbsp; - breadcrumbs

&nbsp; - JSON-LD Product

&nbsp; - кнопка/форма “Оставить заявку” (lead)



\## Хлебные крошки

\- Каталог -> Категория -> Линейка -> Типоразмер

\- Добавить JSON-LD BreadcrumbList (если успевает по MVP — обязательно; иначе в v1, но лучше сразу).



\## Изображения

\- хранение: static/img/catalog/<category\_slug>/<product\_slug>/

\- если image\_path пустой — placeholder.



