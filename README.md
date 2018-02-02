# Nice Django & Tornado & Vue.js Project Template

A nice web project template featured Django, Tornado and Vue.js 2.0+, webpack 2.0+.

Table of Contents
-----------------

* [Nice Django &amp; Tornado &amp; Vue\.js Project Template](#nice-django--tornado--vuejs-project-template)
  * [Features](#features)
  * [How to use this project template](#how-to-use-this-project-template)
    * [The Django template](#the-django-template)
    * [The Tornado template](#the-tornado-template)
    * [Hobgoblin: Tornado &amp; Django integrated with examples](#hobgoblin-tornado--django-integrated-with-examples)
    * [Environment variables](#environment-variables)
  * [Frontend building instructions](#frontend-building-instructions)
    * [Command line env variables and options](#command-line-env-variables-and-options)
    * [TypeScript support](#typescript-support)
  * [Deployment instructions](#deployment-instructions)
  * [DISCLAIMER](#disclaimer)

Created by [gh-md-toc](https://github.com/ekalinin/github-markdown-toc.go).

## Features

Django:

- Loading environment variables from `.env` file.
- Config database and email settings using URL style, like [dj_database_url][dj-database-url] and [dj_email_url][dj-email-url].
- Simple single settings.py file, which can be easily extended to use multiple files.
- Layout django apps under apps subdirectory, with `manage.py startapp` command patched.
- Optional full functionality static file server with [WhiteNoise](http://whitenoise.evans.io/en/stable/django.html) middleware.
- PostgreSQL database support with psycopg2 as default.
- Carefully and reasonably tweaked logging settings.

Tornado:

- Loading environment variables from `.env` file.
- Config database and email settings using URL style, like [dj_database_url](https://github.com/kennethreitz/dj-database-url) and [dj_email_url](https://github.com/migonzalvar/dj-email-url).
- Optional uvloop and asyncio event loop integrated, enabled by default.
- Optional integration with django enable or disable by an command line option.
- Demo websocket handler and django integrated handler (in the [hobgoblin branch][hobgoblin-branch]).
- Integrated logging configuration with django if django is enabled.
- Feel free to write tornado in any style you are familiar.

Frontend:

- Suitable for both single page applications and multiple page applications.
- Develop a single page at once efficiently.
- TypeScript support.
- Use corresponding HTML template file for each entry if exists, or use the root index.html.
- Bundled axios, lodash and moment plugins for Vue.js.
- `npm run dev` to start a live development server with hot reloading.
- `npm run apidoc` to build impressive api documentation with [Apidoc](http://apidocjs.com/).
  See "package.json" file to find all available npm scripts.
- Well designed frontend files layout, with examples in the [hobgoblin branch][hobgoblin-branch].
- All the above features are done with a well structured and flexible single file
  webpack 2.0+ config, while it's somehow complicated :-)

Deployment:

- Example supervisor configuration for django with gunicorn and gevent worker.
- Example supervisor configuration for tornado server.
- Example nginx configuration with static files served by nginx and dynamic requests pass to backend.
- Utility `run_with_env.sh` command to run any command with specified env file.

Utilities:

There are various utilities under the "utils" directory to help fast development, performance tweaking,
debugging and frontend and backend co-developing.

- `utils.db.kv`: key-value client to use database table as KV store.
- `utils.db.sql`: SQL operation helpers.
- `utils.db.sqla`: utility to handle the connection pessimistic problem when using SQLAlchemy
  and globally shared database connection factory.

- `utils.django.admin`: useful functions and classes to help customizing django admin pages.
- `utils.django.models`: a database model to use database table as KV store.
- `utils.django.api`: Django REST Framework like api view decorator and error handlers.

- `utils.tornado.api`: DjangoJSONEncoder like json encoder and a base api request handler with properly error handling.
- `utils.tornado.celery`: helpers to wait task result asynchronously when using Celery with tornado.

- `utils.confurl`: parse database and email settings using URL style, which can be extended to parse other settings which have similar structure, borrowed from [dj_database_url][dj-database-url] and [dj_email_url][dj-email-url].
- `utils.dotenv`: dotenv parsing utility copied from [django-dotenv][django-dotenv] and [python-dotenv][python-dotenv], which all install themselves as "dotenv" -_-
- `utils.http_status`: Descriptive HTTP status codes, for code readability, copied from Django REST Framework.
- `utils.exceptions`: commonly used API exceptions, borrowed from Django REST Framework.
- `utils.decorators`: various useful decorators to help performance tweaking,
debugging and frontend and backend co-developing.

For more details, just create a project with the template and play with it!

Any issues and feature requests are welcome!

## How to use this project template

To give using examples but keep the project template as clean as possible,
there are three branches maintained simultaneously:

- `master`: Django project template to be used with `django-admin startproject`.
- `tornado`: Tornado project template, use with the `install.py` script from this project.
- `hobgoblin`: Tornado with django integrated project template, with a lot of
  django views and tornado request handlers, utilities usages, and frontend pages examples.
  Use with the `install.py` script from this project.

See the following instructions for detail usages.

### The Django template

```bash
django-admin.py startproject \
    --template https://github.com/jxskiss/nice-pyvue-template/archive/master.zip \
    --extension=.py,.json,.md,.conf,.env \
    <project_name>
cd project_name
pip install -r requirements.txt
cp example.env .env

# Please edit the .env file as needed

./manage.py migrate
./manage.py createsuperuser

# build frontend files
cd frontend/
npm install && npm run build

# play with django server
# open with your browser: "http://127.0.0.0:8000/", "http://127.0.0.1:8000/admin/"
cd ..
./manage.py runserver 0.0.0.0:8000
```

### The Tornado template

```bash
TARGET=tornado PROJECT_NAME=<project_name> python -c "$(
    curl -fsSL https://raw.githubusercontent.com/jxskiss/nice-pyvue-template/hobgoblin/install.py )"
cd project_name
pip install -r requirements.txt
cp example.env .env

# Please edit the .env file as needed

# build frontend files
cd frontend/
npm install && npm run build

# paly with tornado server
# open with your browser: "http://127.0.0.1:8080/"
cd ../
./server.py --port=8000
```

### Hobgoblin: Tornado & Django integrated with examples

```bash
TARGET=hobgoblin PROJECT_NAME=<project_name> python -c "$(
    curl -fsSL https://raw.githubusercontent.com/jxskiss/nice-pyvue-template/hobgoblin/install.py )"
cd project_name
pip install -r requirements.txt
cp example.env .env

# Please edit the .env file as needed

./manage.py migrate
./manage.py createsuperuser

# build frontend files
cd frontend/
npm install && npm run build

# to play with django or tornado, go back to the project root
cd ..

# play with django server, open with your browser after starting server:
# "http://127.0.0.0:8000/", "http://127.0.0.1:8000/demo/" and "http://127.0.0.1:8000/admin/"
./manage.py runserver 0.0.0.0:8000

# play with tornado server, open with your browser aftere starting server:
# "http://127.0.0.1:8001/tornado/hello" and "http://127.0.0.1:8001/tornado/hello-socket"
./server.py --port=8001

# note this is STRONGLY DISCOURAGED for production
# play with tornado integrated with django in debug mode, open with your browser:
# "http://127.0.0.1:8001/tornado/hello-django" and "http://127.0.0.1:8001/admin/"
./server.py --port=8001 --debug
```

### Environment variables

```bash
export DEBUG=False
export LOG_LEVEL=INFO
export TIME_ZONE=Asia/Shanghai

export SECRET_DATABASE_URL=
export SECRET_EMAIL_URL=
export SECRET_KEY=
```

## Frontend building instructions

```bash
cd frontend/

# install dependencies
npm install

# live development server with hot reloading
npm run dev

# use specified port and pass "/api/" requests to backend
API=8080 BACKEND=127.0.0.1:8000 npm run dev

# build for development and watch changes
npm run watch

# build for production with minification and source map
npm run build

# build api docs with apidocjs
npm run apidoc
```

### Command line env variables and options

Some helpful command line environment variables and options are supported.

For *nix systems, use `VAR=someValue npm run script`.

On Windows, cmd and powershell do not support command line environment variables,
you need to use the command line options: `npm run script -- --env.var=someValue`.

```bash
# run dev server with specified port
PORT=8000 npm run dev
# or
npm run dev -- --env.port=8000

# call dev/watch/build script for specified single page only
PAGE=index npm run dev
PAGE=dev-single npm run dev
PAGE=iview-admin npm run build
# or
npm run dev -- --env.page=index
npm run dev -- --env.page=dev-single
npm run build -- --env.page=iview-admin

# to view the bundle analyzer report after build for production
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


## DISCLAIMER

Most of the ideas and codes in this project are copied from other projects,
many thanks to their contributors. Copy rights are reserved for the original
developers.

This project is provided AS-IS, though anyone is welcomed to use the project
and the developer is trying his best to make things work right.


[master-branch]: https://github.com/jxskiss/nice-pyvue-template/
[tornado-branch]: https://github.com/jxskiss/nice-pyvue-template/tree/tornado
[dj-email-url]: https://github.com/migonzalvar/dj-email-url
[dj-database-url]: https://github.com/kennethreitz/dj-database-url
[django-dotenv]: https://github.com/jpadilla/django-dotenv
[python-dotenv]: https://github.com/theskumar/python-dotenv
[hobgoblin-branch]: https://github.com/jxskiss/nice-pyvue-template/tree/hobgoblin
[vue-2.5-typescript]: https://medium.com/the-vue-point/upcoming-typescript-changes-in-vue-2-5-e9bd7e2ecf08
[ts-loader-vue-issue]: https://github.com/vuejs/vue-loader/issues/109
[Vetur]: https://github.com/vuejs/vetur
