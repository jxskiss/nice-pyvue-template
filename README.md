# Nice Django & Tornado & Vue.js Project Template

A very nice web project template featured Django, Tornado and Vue.js 2.0+, webpack 2.0+.

## Features

Django:

- Django 1.11
- Load environment variables from `.env` with [django-dotenv](https://github.com/jpadilla/django-dotenv).
- Config database and email settings using [dj_database_url](https://github.com/kennethreitz/dj-database-url) and [dj_email_url](https://github.com/migonzalvar/dj-email-url).
- Simple single settings.py file, which can be easily extended to use multiple files.
- Layout django apps under apps subdirectory, with `manage.py startapp` command patched.
- Full functionality static file server with [WhiteNoise](http://whitenoise.evans.io/en/stable/django.html) middleware.
- PostgreSQL database support with psycopg2.

Tornado:

- Optional integration with django enable or disable by an command line option.
- Demo websocket handler and django integrated handler.
- Integrated logging configuration with django if django is enabled.
- Feel free to write tornado in any style you are familiar.
- Simply remove file `server.py` and directory `handlers` to drop any tornado related things.

Frontend:

- Single file yet full functionality and very flexible webpack 2.0+ config.
- Well designed frontend files layout.
- Public directory aimed to place compiled frontend files with git managed
  to avoid building again in production environment.
- Suitable for both single page application and multiple page application.
- `npm run dev` to start a live development server with hot reloading.
- `npm run apidoc` to build impressive api documentation with [Apidoc](http://apidocjs.com/).
- See package.json to find all available npm commands.

Deployment:

- Example supervisor configuration for django with gunicorn and gevent worker.
- Example supervisor configuration for tornado server.
- Example nginx configuration with static files served by nginx and dynamic requests pass through to backend.
- Utility `run_with_env.sh` command to run any command with specified env file.

For more details, just create a project with this template and play with it!

Any issues and feature requests are welcome!


## How to use this project template

```bash
django-admin.py startproject \
    --template https://github.com/jxskiss/nice-pyvue-template/archive/master.zip \
    --extension=.py,.json,.js,.md,.conf,.env \
    project_name
cd project_name
chmod +x manage.py server.py run_with_env.sh
pip install -r requirements.txt
cp example.env .env; vim .env

# after change your .env file correctly
./manage.py migrate

# build frontend files
npm install && npm run build

# play with django server
# open your browser and browse:
# "http://127.0.0.0:8000/", "http://127.0.0.1:8000/demo/" and "http://127.0.0.1:8000/admin/"
./manage.py runserver 0.0.0.0:8000

# play with tornado server
# open your browser and browse:
# "http://127.0.0.1:8001/tornado/hello" and "http://127.0.0.1:8001/tornado/hello-socket"
./server.py --port=8001

# play with tornado integrated with django in debug mode
# note this is STRONGLY DISCOURAGED for production
# open your browser and browse:
# "http://127.0.0.1:8001/tornado/hello-django" and "http://127.0.0.1:8001/admin/"
./server.py --port=8001 --debug
```


## Deployment instructions

See `server_configs/supervisor.conf` and `server_configs/nginx.conf` for details.

### Environment variables

```bash
export DJANGO_DEBUG=False
export DJANGO_LOG_LEVEL=INFO
export DJANGO_TIMEZONE=Asia/Shanghai

# database connection string used by dj_database_url and sqlalchemy
export DJANGO_DATABASE_URL=
# email url string used by dj_email_url for email settings
export DJANGO_EMAIL_URL=
# secret key
export DJANGO_SECRET_KEY=
```

## Frontend build Instructions

```bash
# install dependencies
npm install

# live development server with hot reloading
npm run dev

# build for development
npm run build

# build for development and watch changes
npm run watch

# build for production with minification
npm run release

# build api documentations written with apidoc
npm run apidoc
```
