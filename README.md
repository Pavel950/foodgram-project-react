# Foodgram
![Main Foodgram workflow](https://github.com/Pavel950/foodgram-project-react/actions/workflows/main.yml/badge.svg)


## Описание
Foodgram - сервис для публикации рецептов.  
Аутентифицированным пользователям проект позволяет добавлять новые рецепты на сайт, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Информацию о собственных рецептах можно изменить или вовсе удалить с сайта.  
Аутентифицированным пользователям сайта также доступен сервис «Список покупок», который позволяет создавать список продуктов, которые нужно купить для приготовления выбранных блюд.  
Для каждого рецепта нужно обязательно указать название, текстовое описание, время приготовления блюда; выбрать ингредиенты из предопределенного списка и их количество, добавить изображение. Каждый рецепт отмечается одним или несколькими из предустановленных тегов. Редактировать списки ингредиентов и тегов имеет право только администратор.  
Анонимным пользователям проект позволяет просматривать рецепты и страницы пользователей.


## Автор проекта

Павел Гусев ([GitHub](https://github.com/Pavel950/))

## Стек проекта
Python, Django, Django REST framework, PostgreSQL, Nginx, Gunicorn, Docker

## Информация для доступа к проекту
### Адрес сервера:  
https://foodgram-proj.sytes.net  
### Данные администратора:
- логин: super
- email: super@1.ru
- пароль: admin

## Как запустить проект

**Клонировать из репозитория в папку проекта на целевом сервере:**  
- docker-compose.production.yml (файл конфигурации)  
- docs (директория с файлами документации ReDoc)
- data (директория с данными для заполнения БД)


**Cоздать файл .env в папке проекта; он должен содержать следующие значения:**

```
#имя пользователя базы данных
POSTGRES_USER=name
#пароль пользователя базы данных
POSTGRES_PASSWORD=passwd
#имя базы данных
POSTGRES_DB=db_name
# адрес, по которому Django будет соединяться с базой данных
# или имя контейнера, где запущен сервер БД
DB_HOST=db
# порт, по которому Django будет обращаться к базе данных
DB_PORT=5432
# список ip-адресов, доменов, на которых будет развернут проект - # через запятую без пробелов
ALLOWED_HOSTS=1.1.1.1,example.org
# включение/выклечение режима отладки
DEBUG=True
# флаг, определяющий подключаемую БД (PostgreSQL/SQLite)
DB_SQLITE=False
# SECRET_KEY, определяемый в файле settings.py django-проекта
SECRET_KEY=secret_value
```

**Запустить сеть контейнеров:**
```
docker compose -f docker-compose.production.yml up -d
```

**Применить миграции в контейнере backend:**

```
docker compose -f docker-compose.production.yml exec backend python manage.py migrate
```

**Создать и скопировать статику в контейнере backend:**

```
docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic

docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
```

**Импортировать данные из директории data в БД в контейнере backend:**

```
docker compose -f docker-compose.production.yml exec backend python manage.py import_data
```
