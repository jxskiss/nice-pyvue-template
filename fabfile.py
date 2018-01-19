# -*- coding:utf-8 -*-
from __future__ import print_function
from fabric.api import lcd, local, hide
import functools
import json
import os
import re
import sys

_JS_API_HEADER = """
/**
 * Auto generated API module by Fabric task:
 *     {cmd} {args}
 * See api.base.js for details and usage information.
 */

import makeApiModule from '@/common/api.base'
""".lstrip().format(
    cmd=os.path.basename(sys.argv[0]),
    args=' '.join(sys.argv[1:])
)

_JS_MODULE_TMPL = """
const {module}ApiDefs = {defs}

export const {module}Api = new (makeApiModule({module}ApiDefs))()
"""


def _lcd_frontend(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with lcd('frontend'):
            return func(*args, **kwargs)

    return wrapper


@_lcd_frontend
def install_cnpm():
    """
    Install utility "cnpm" globally.
    """
    local('npm install -g cnpm --registry=https://registry.npm.taobao.org')  # noqa


@_lcd_frontend
def npm_install():
    """
    Install npm packages listed in frontend/package.json.
    """
    local('cnpm install')


@_lcd_frontend
def npm_run(script, *options):
    """
    Run npm script, optionally with additional options.
    """
    cmd = 'npm run %s' % script
    if options:
        cmd += ' -- '
        for opt in options:
            cmd += ' --' + opt
    local(cmd)


def npm_dev(page=''):
    """
    Run webpack dev server, optionally for specified page.
    """
    options = []
    if page:
        options.append('env.page=%s' % page)
    npm_run('dev', *options)


def make_js_api():
    """
    Make API js module from apidocjs(-like) docstrings.
    """
    from collections import defaultdict
    from six.moves.urllib_parse import urlparse as urlparse
    api_pattern1 = re.compile(r"""
        # apidocjs's marker
        @api\s+
        # request method
        {(?P<method>\w+)}\s+
        # resource path
        (?P<path>/[\w/:]+)\s+
        # api group and name
        (?P<group>\w+):(?P<name>\w+)
        """, re.VERBOSE)

    api_pattern2 = re.compile(r"""
        # apidocjs's marker
        @api\s+
        # request method
        {(?P<method>\w+)}\s+
        # resource path
        (?P<path>/[\w/:]+).+?
        # api name
        @apiName\s+(?P<name>\w+).+?
        # api group
        @apiGroup\s+(?P<group>\w+)
        """, re.VERBOSE | re.DOTALL | re.MULTILINE)
    api_pattern3 = re.compile(r"""
        # apidocjs's marker
        @api\s+
        # request method
        {(?P<method>\w+)}\s+
        # resource path
        (?P<path>/[\w/:]+).+?
        # api group
        @apiGroup\s+(?P<group>\w+).+?
        # api name
        @apiName\s+(?P<name>\w+)
        """, re.VERBOSE | re.DOTALL | re.MULTILINE)

    py_doc_pattern = re.compile(r"""
        (?:\"\"\".+?\"\"\")
        |
        (?:\'\'\'.+?\'\'\')
        """, re.VERBOSE | re.DOTALL | re.MULTILINE)

    cstyle_doc_pattern = re.compile(r"""
        /\*.+?\*/
        """, re.VERBOSE | re.DOTALL | re.MULTILINE)

    def get_doc_strings(filename):
        ext = os.path.splitext(filename)[-1]
        pattern = None
        if ext == '.py':
            pattern = py_doc_pattern
        elif ext in ('.js', '.json'):
            pattern = cstyle_doc_pattern
        if not pattern:
            return
        with open(filename, 'r', encoding='utf8') as fd:
            docstrings = pattern.findall(fd.read())
        yield from docstrings

    include_patterns = [
        re.compile(r'^[^.].*\.py$'),
        re.compile(r'^[^.].*\.json$'),
    ]
    exclude_patterns = [
        re.compile('frontend'),
    ]

    def should_process(entry, is_file):
        if exclude_patterns:
            for pat in exclude_patterns:
                if pat.search(entry):
                    return False
        if include_patterns and is_file:
            for pat in include_patterns:
                if pat.search(entry):
                    return True
            return False
        return True

    def get_base_path():
        package = json.load(open('frontend/package.json'))
        url = package.get('apidoc', {}).get('url')
        if url:
            url = urlparse(url)
            return url.path.rstrip('/')
        return ''

    def walk(root):
        entries = os.listdir(root)
        for ent in entries:
            path = os.path.join(root, ent)
            is_file = os.path.isfile(path)
            if not should_process(ent, is_file):
                continue
            if is_file:
                yield path
            else:
                yield from walk(path)

    base_api_path = get_base_path()
    files = walk('./')
    api_defs = defaultdict(dict)
    for fn in files:
        for docstring in get_doc_strings(fn):
            api = None
            for pat in (api_pattern1, api_pattern2, api_pattern3):
                api = pat.search(docstring)
                if api:
                    break
            if not api:
                continue
            group = api.group('group')
            group = group[0].lower() + group[1:]
            name = api.group('name')
            name = name[0].lower() + name[1:]
            api_defs[group][name] = {
                'method': api.group('method'),
                'url': base_api_path + api.group('path')
            }

    # redirect Fabric's output to stderr
    stdout_bak = sys.stdout
    sys.stdout = sys.stderr
    if api_defs:
        stdout_bak.write(_JS_API_HEADER)
    for group, defs in api_defs.items():
        stdout_bak.write(_JS_MODULE_TMPL.format(
            module=group, defs=json.dumps(defs, indent=2)))


def make_rest_api(resource, path_prefix, plural=None):
    """
    Make restful API js module for resource.

    References:
        https://github.com/bolasblack/http-api-guide
        http://www.vinaysahni.com/best-practices-for-a-pragmatic-restful-api
    """
    path_prefix = path_prefix.rstrip('/')
    if not plural:
        plural = resource

    def _name(action):
        return action.format(resource.title().replace('/', ''))

    def _pname(action):
        return action.format(plural.title().replace('/', ''))

    def _url(path):
        return path_prefix + path.format(plural.strip('/'))

    api_defs = {
        # retrieve full list of resource
        _pname('getAll{}'): {'method': 'GET', 'url': _url('/{}')},
        # retrieve pageable list of resource, query params: page=int, size=int
        _pname('getPageable{}'): {'method': 'GET', 'url': _url('/{}')},
        # retrieve a resource with specific id
        _name('get{}'): {'method': 'GET', 'url': _url('/{}/:id')},
        # create a new resource
        _name('create{}'): {'method': 'POST', 'url': _url('/{}')},
        # update a resource with specific id
        _name('update{}'): {'method': 'PUT', 'url': _url('/{}/:id')},
        # delete a resource with specific id
        _name('delete{}'): {'method': 'DELETE', 'url': _url('/{}/:id')}
    }
    module = resource.replace('/', '')
    module = module[1].lower() + module[1:]

    # redirect Fabric's output to stderr
    stdout_bak = sys.stdout
    sys.stdout = sys.stderr
    stdout_bak.write(_JS_API_HEADER)
    stdout_bak.write(_JS_MODULE_TMPL.format(
        module=module, defs=json.dumps(api_defs, indent=2)))


def ngx_spa_loc(page=''):
    """
    Make Nginx location config for single page app.
    """
    paths = page.split('/')
    page = '/'.join(paths[:-1])
    if paths and paths[-1] != 'index':
        page += '/' + paths[-1]
    if page:
        page += '/'

    tmpl = """
    location /PAGE {
        alias {{ project_directory }}/frontend/dist/PAGE;
        index index.html index.htm;
        try_files $uri $uri/ index.html index.htm =404;
    }
    """
    # redirect Fabric's output to stderr
    stdout_bak = sys.stdout
    sys.stdout = sys.stderr
    stdout_bak.write(tmpl.replace('PAGE', page))


def make_proxy_loc(location, upstream, *backends):
    """
    Make Nginx proxy location config for upstream.
    """
    upstream_tmpl = """
upstream UPSTREAM {
    server SERVERS;
}
"""
    # redirect Fabric's output to stderr
    stdout_bak = sys.stdout
    sys.stdout = sys.stderr
    if upstream and backends:
        stdout_bak.write(
            upstream_tmpl.replace('UPSTREAM', upstream)
            .replace('SERVERS', ';\n    server '.join(backends))
        )

    location_tmpl = """
location LOCATION {
    # client_max_body_size    10m;

    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    # proxy_set_header X-Forwarded-Ssl on;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";

    proxy_read_timeout      60s;
    proxy_connect_timeout   60s;
    proxy_http_version      1.1;
    proxy_redirect          http:// $scheme://;

    proxy_pass http://UPSTREAM;
}
"""
    stdout_bak.write(
        location_tmpl.replace('LOCATION', location)
        .replace('UPSTREAM', upstream or backends[0])
    )


def runtests():
    local("python -m unittest discover -s tests -p test*.py")
