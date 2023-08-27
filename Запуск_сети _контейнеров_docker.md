# Cборка проекта в сети контейнеров

## Содержание

- [Локальная сборка](#сборка-образов-в-локальной-сети-контейнеров)
- [Запуск и сборка контейнеров](#запуск)
- [Сборка статики](#сборка-статики)
- [Пред установки](#пред-установки-перед-запуском-сайта)
- [Деплой](#деплой)
- [Авторизация Docker Hub](#авторизация-в-docker-hub)
- [Push образова](#push-образов)
- [Важные изменения проекта](#важные-изменения-проекта)

## Сборка образов в локальной сети контейнеров

### Backend

```bash
cd backend
docker build -t aleksti/recipe_blog_backend .
               #username в докер хаб       #точка - текущая папки
                        # название образа
```

### Frontend

```bash
cd ../frontend/
docker build -t aleksti/recipe_blog_frontend .
```

### Infra

```bash
cd ../infra/
docker build -t aleksti/recipe_blog_gateway .
```

### Запуск

Перед запуском не забудьте создать файл .env в папке infra/тут и поместить свои ключи к проекту.

```bash
docker compose down && docker compose up --build
```

### Сборка статики

```bash
# узнать имя контэйнера бэкенда
docker container ls
# пример:
    # infra-backend-1

# зайти в контейнер:
docker exec -it infra-backend-1 bash
# появится режим командной строки внутри контейнера:
# пример:
    # root@a78a3f313642:/app#
python manage.py collectstatic
# 163 static files copied to '/app/collected_static'

# копирование статики в связанную папку с volumes backend_static
cp -r /app/collected_static/. /backend_static/static/
```

### Пред установки перед запуском сайта

Теперь можно провести миграции и создать суперюзера:

```bash
python manage.py migrate  # миграции
python manage.py createsuperuser   # суперюзер
```

Сайт станет доступен: http://localhost:10000/recipes

## Деплой

Общие рекомендации.

Прежде чем пушить образы, нужно авторизоваться

### Авторизация в docker hub

Если не авторизовались ранее.

```bash
docker login
# А можно сразу указать имя пользователя:
docker login -u username
```

### Push образов

Push образов(image) в Docker Hub

```bash
docker push username/recipe_blog_backend
docker push username/recipe_blog_frontend
docker push username/recipe_blog_gateway
```

### Важные изменения проекта

Образы готовы, приутствуют в докер хаб, теперь, нужно изменить часть проекта, под свои значения.

В файле **infra/docker-compose.production.yml** все значения **image: aleksti/recipe_blog_gateway** нужно изменить, aleksti на ваш username в Docker Hub.

Так же в этом же файле, изменить:

```bash
  nginx:
    image: username/recipe_blog_gateway  # <- username
    ports:
      - "10000:80" # порт 10_000 изменить на ваш во внешнем nginx на сервере.
```

### Сервер и секреты

На сервере в подготовленной папке под проект, должны быть созданы файлы **.env** и **docker-compose.production.yml** и скопированы данные из локального проекта(ctrl + C / ctrl + V)

### Git Hub настройки для проекта и workflows

Файл main.yml не рекомендуется использовать такой же как в проекте, лишь как референс.
Workflows вы должны написать самостоятельно, под свои задачи и ресурсы которыми обладаете.

### Запуск CI/CD

При push проекта, workflows запустит цепочку команд, проверит проект по PEP8 и обновит образы на Docker Hub и задеплоит на сервер.

Для этого необходимо указать в **main.yml** ветку, на которую будет реагировать код.

```bash
on:
  push:
    branches:
      - master # <- указать ветку, тригер

```
