# Проект Foodgram

Добро пожаловать в Foodgram! Это ваш уникальный ресурс для создания, поиска и обмена рецептами. 

## 1. О проекте 
Foodgram - это платформа для любителей готовить и делиться своими кулинарными шедеврами. Здесь вы можете создавать, искать и сохранять рецепты, а также делиться ими с другими пользователями.

## 2. Как начать
Для начала использования Foodgram просто перейдите по [ссылке](https://f00dgram.serveblog.net/). Если у вас нет аккаунта, вы можете зарегистрироваться, а затем войти в свой аккаунт.

## 3. Функционал для авторизованных пользователей
Главная страница: Просматривайте последние рецепты и получайте вдохновение.
Страница пользователя: Узнайте больше о других участниках и их рецептах.
Страница рецепта: Получайте полную информацию о рецепте, а также добавляйте его в избранное и список покупок.
Мои подписки: Следите за обновлениями ваших любимых авторов.
Избранное: Собирайте ваши любимые рецепты в одном месте.
Список покупок: Планируйте свои покупки, основываясь на ингредиентах из ваших рецептов.
Создать рецепт: Добавляйте свои уникальные рецепты и делитесь ими с сообществом.

## 4. Технические детали
База данных: PostgreSQL.
Веб-сервер: Nginx.
Серверное приложение: Django + Gunicorn.
Хранение данных: Volumes.

# 5. Как работать с репозиторием финального задания
1. Клонируйте репозиторий
```
git@github.com:OFF1GHT/foodgram-project-react.git
```

2. Переименуйте файл '.env.example' на 'env' и подставте свои данные.


3. Добавьте секреты в GitHub Action:
- DOCKER_USERNAME - ваш логин на DockerHub
- DOCKER_PASSWORD - ваш пароль на DockerHub
- SSH_PASSPHRASE - пароль от удаленного сервера
- HOST - IP адрес сервера
- USER - имя пользователя на удаленном сервере
- SSH_KEY - приватный ключ для подключения к удаленному серверу
- TELEGRAM_TO - id пользователя в Telegram
- TELEGRAM_TOKEN - токен Telegram-бота

## На удаленном сервере

4. Запустите проект:
```
sudo docker compose -f docker-compose.production.yml up -d
```

5. Подключитесь к удаленному серверу и выполните эти команды:
```
sudo apt update
sudo apt install curl
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo apt-get install docker-compose-plugin
```

6. В директорию 'foodgram' добавте файл docker-compose.production.yml.

7. Запустите Docker Compose в режиме демона:
```
sudo docker compose -f docker-compose.production.yml up -d
```

8. Выполните миграции, соберите статику, скопируйте ее в /app/collected_static/:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/static/. /app/collected_static/
```

9. Обновите настройки Nginx. Откройте файл конфигурации: 
```
sudo nano /etc/nginx/sites-enabled/default
```

10. Добавьте новые настройки:
```
location / {
    proxy_set_header Host $http_host;
    proxy_pass http://127.0.0.1:9000;
}
```

11. Проверьте работоспособность:
```
sudo nginx -t
```

12. Перезагрузите конфигурацию Nginx:
```
sudo systemctl reload nginx
```

## Запуск проекта на локальном хосте

1. Клонируйте репозиторий:
```
git@github.com:OFF1GHT/foodgram-project-react.git
```

2. Запустите миграции:
```
docker compose run web python manage.py migrate
```

3. Соберите статику:
```
docker compose exec backend python manage.py collectstatic
docker compose exec backend cp -r /app/static/. /app/collected_static/
```

4. Переименуйте файл '.env.example' на 'env' и подставте свои данные.

5. Запустите контейнеры:
```
docker compose up -d
```

6. Остановка контейнера и повторный запуск:
```
docker container stop имя_контейнера
docker container start имя_контейнера
```

7. Проект доступен по адресу 'http://localhost'

## Чем отличается продакшн-версия от обычной и в каком случае нужно использовать ту или иную верисию.

### Продакшн-версия
Продакшн версию стоит использоват когда вы хотите предоставить доступ реальным пользователям.

### Обычная версия
Обычныую верисию стоит использовать для тестирования и разработки новых функций.

## Автор проекта: OFF1GHT

## Используемые технолгии:
- Python
- Postgres
- Docker
- Nginx
- Gunicorn
- Django
