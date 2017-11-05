# Nice Django & Tornado & Vue.js Project Template

A very nice web project template featured Django, Tornado and Vue.js 2.0+, webpack 2.0+.

## Features

Django:

- Django 1.11
- Load environment variables from `.env` with [django-dotenv](https://github.com/jpadilla/django-dotenv).
- Config database and email settings using [dj_database_url](https://github.com/kennethreitz/dj-database-url) and [dj_email_url](https://github.com/migonzalvar/dj-email-url).
- Simple single settings.py file, which can be easily extended to use multiple files.
- Layout django apps under apps subdirectory, with `manage.py startapp` command patched.
- Optional full functionality static file server with [WhiteNoise](http://whitenoise.evans.io/en/stable/django.html) middleware.
- PostgreSQL database support with psycopg2.

Tornado:

- Optional integration with django enable or disable by an command line option.
- Demo websocket handler and django integrated handler.
- Integrated logging configuration with django if django is enabled.
- Feel free to write tornado in any style you are familiar.
- Simply remove file `server.py` and directory `handlers` to drop any tornado related things.

Frontend:

- Suitable for both single page application and multiple page application.
- TypeScript support.
- Use corresponding HTML template file for each entry if exsits, or use the root index.html.
- `npm run dev` to start a live development server with hot reloading.
- `npm run apidoc` to build impressive api documentation with [Apidoc](http://apidocjs.com/).
  See "package.json" file to find all available npm scripts.
- Well designed frontend files layout.
- All the above features in well structured and flexible single file webpack 2.0+ config.

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
./manage.py createsuperuser

# build frontend files
cd frontend/
npm install && npm run build

# build api docs with apidocjs
npm run apidoc

# to play with django or tornado, go back to the project root
cd ..

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
cd frontend/

# install dependencies
npm install

# live development server with hot reloading
npm run dev

# build for development and watch changes
npm run watch

# build for production with minification and source map
npm run build

# build api docs with apidocjs
npm run apidoc
```

### Command line ENV and options

Some helpful command line environment variables and options are supported.

For *nix systems, use `VAR=someValue npm run script`.

On Windows, cmd and powershell do not support command line environment variables,
you need to use the command line options `npm run script -- --env.var=someValue`.

```bash
# run dev server with specified port
PORT=8000 npm run dev
# or
npm run dev -- --env.port=8000

# call dev/watch/build script for specified single page only
PAGE=index npm run dev
PAGE=demoapp npm run build
# or
npm run dev -- --env.page=index
npm run build -- --env.page=demoapp

# view the bundle analyzer report after build for production
npm run build -- --env.report
```

### TypeScript support

With Vue.js version 2.5+, TypeScript integration has been [greatly improved][vue-2.5-typescript].

`.ts` and `.js` entries are both supported, but if you use TypeScript in
vue single-file component (`<script lang="ts">`), the entry must be a `.ts` file,
or the ts-loader will throw ["could not find file: *.vue" errors][ts-loader-vue-issue].

If you are using VSCode, the awesome [Vetur][] extension is recommended by the Vue.js author,
with Vetur you will get greatly improved autocompletion suggestions and even
type hints when using plain JavaScript in Vue components!

## Deployment instructions

See `server_configs/supervisor.conf` and `server_configs/nginx.conf` for details.

[vue-2.5-typescript]: https://medium.com/the-vue-point/upcoming-typescript-changes-in-vue-2-5-e9bd7e2ecf08
[ts-loader-vue-issue]: https://github.com/vuejs/vue-loader/issues/109
[Vetur]: https://github.com/vuejs/vetur
