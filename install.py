#!/usr/bin/python
# -*- coding:utf-8 -*-

import os
import random
import re
import string
import subprocess
import tempfile
import zipfile

TARGETS = ['django', 'tornado', 'hobgoblin']
BASE_URL = 'https://github.com/jxskiss/nice-pyvue-template/archive'
TPL_EXTENSIONS = ['.py', '.json', '.js', '.md', '.conf', '.env']

inputs = {}
variables = {}


def pre_action():
    global inputs, variables

    target = os.getenv('TARGET', '').strip().lower()
    while not target:
        target = input('Target branch (django, tornado, hobgoblin): ').strip()
        if not target:
            print('Error: target branch must be provided.')
        elif target not in TARGETS:
            print('Error: unknown target: "%s".' % target)
    inputs['target'] = target

    proj_name = os.getenv('PROJECT_NAME', '').strip().lower()
    while not proj_name:
        pn = input('Project Name: ').strip()
        if not pn:
            print('Error: project name must be provided.')
        elif re.search(r'\s+', pn):
            print('Error: project name cannot contain blank characters.')
        else:
            if re.search(r'-', pn):
                print('Warning: the "-" in project name will be replaced '
                      'by "_".')
                pn = pn.replace('-', '_')
            proj_name = pn
    inputs['project_name'] = proj_name

    variables['project_name'] = proj_name
    variables['project_name_title'] = proj_name.replace('_', ' ').title()
    variables['project_directory'] = os.path.normpath(
        os.path.abspath(proj_name))
    _chars = list(string.ascii_letters + '@%*=&!#^' * 5)
    random.shuffle(_chars)
    variables['secret_key'] = ''.join(_chars[:50])


def post_action():
    installer = os.path.join(inputs['project_name'], 'install.py')
    if os.path.exists(installer):
        os.remove(installer)


def render_templates():
    patterns = {
        'project_name': re.compile(r'\{\{\s*project_name\s*\}\}'),
        'project_name_title': re.compile(
            r'\{\{\s*project_name\s*\|\s*title\s*\}\}'),
        'project_directory': re.compile(r'\{\{\s*project_directory\s*\}\}'),
        'secret_key': re.compile(r'\{\{\s*secret_key\s*\}\}')
    }

    def walk(path):
        for top, dirs, files in os.walk(path):
            for fn in files:
                _, ext = os.path.splitext(fn)
                if ext and ext in TPL_EXTENSIONS:
                    with open(os.path.join(top, fn)) as fd:
                        contents = fd.read()
                    for k, p in patterns.items():
                        contents = re.sub(p, variables[k], contents)
                    with open(os.path.join(top, fn), 'w') as fd:
                        fd.write(contents)
            for dn in dirs:
                walk(os.path.join(top, dn))

    walk(os.path.abspath(inputs['project_name']))


def extract_zip(file, path):
    zf = zipfile.ZipFile(file, 'r')

    def memebers():
        prefix = os.path.commonprefix(zf.namelist())
        for zipinfo in zf.infolist():
            zipinfo.filename = zipinfo.filename.replace(prefix, '', 1)
            if zipinfo.filename:
                yield zipinfo

    zf.extractall(path, members=memebers())
    zf.close()


def main():
    pre_action()

    if inputs['target'] == 'tornado':
        if os.path.exists(inputs['project_name']):
            if os.listdir(inputs['project_name']):
                raise SystemExit(
                    'Error: directory %s already exists and not empty.')
        else:
            os.mkdir(inputs['project_name'])

        url = BASE_URL + '/tornado.zip'
        tmp_fn = tempfile.mktemp()
        try:
            subprocess.check_call('wget -O {} {}'.format(tmp_fn, url),
                                  shell=True)
            extract_zip(tmp_fn, inputs['project_name'])
        finally:
            if os.path.exists(tmp_fn):
                os.remove(tmp_fn)
        render_templates()

    # django and the hobgoblin
    else:
        branch = 'master' if inputs['target'] == 'django' else 'hobgoblin'
        cmd = (
            "django-admin.py startproject "
            "--template {base}/{branch}.zip "
            "--extension={exts} {proj_name}"
            .format(
                base=BASE_URL,
                branch=branch,
                exts=','.join(TPL_EXTENSIONS),
                proj_name=inputs['project_name']))
        subprocess.check_call(cmd, shell=True)

    post_action()
    print('Success, enjoy!')


if __name__ == '__main__':
    main()
