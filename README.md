# The {{ project_name|title }} Project


## How to use this project template

```bash
django-admin.py startproject \
    --template https://github.com/jxskiss/nice-pyvue-template/archive/master.zip \
    --extension=.py,.json,.js,.md,.conf,.env \
    <project_name>
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

``` bash
# install dependencies
npm install

# live development server with hot reload
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
