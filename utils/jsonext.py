"""
https://gist.github.com/liftoff/ee7b81659673eca23cd9fc0d8b8e68b7
Copyright: Dan McDougall <daniel.mcdougall@liftoffsoftware.com>

Removes C-style comments and trailing commas from string.

Support "@import(another.json)" syntax.

.. code-block:: javascript

    {
        // A comment!  You normally can't put these in JSON
        "testing": {
            "foo": "bar", // <-- A trailing comma!  No worries.
        }, // <-- Another one!
        /*
        This style of comments will also be safely removed
        */
    }

"""

import json
import os
import re

IMPORT_RE = re.compile(r'"@import\((.+)\)"')
COMMENTS_RE = re.compile(
    r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
    re.DOTALL | re.MULTILINE
)
TRAILING_OBJECT_COMMAS_RE = re.compile(
    r'(,)\s*}(?=([^"\\]*(\\.|"([^"\\]*\\.)*[^"\\]*"))*[^"]*$)')
TRAILING_ARRAY_COMMAS_RE = re.compile(
    r'(,)\s*\](?=([^"\\]*(\\.|"([^"\\]*\\.)*[^"\\]*"))*[^"]*$)')


def load_file(path, *, cls=None, object_hook=None, parse_float=None,
              parse_int=None, parse_constant=None, object_pairs_hook=None,
              **kw):
    return load(open(path, 'r', encoding='utf8'),
                cls=cls, object_hook=object_hook,
                parse_float=parse_float, parse_int=parse_int,
                parse_constant=parse_constant,
                object_pairs_hook=object_pairs_hook, **kw)


def load(fp, *, cls=None, object_hook=None, parse_float=None,
         parse_int=None, parse_constant=None, object_pairs_hook=None, **kw):
    if hasattr(fp, 'name') and fp.name != '':
        root = os.path.dirname(os.path.abspath(fp.name))
    else:
        root = os.path.abspath(os.path.curdir)
    content = fp.read()
    content = _replace_import(content, root)
    content = _remove_comment(content)
    content = _fix_trailing_commas(content)
    return json.loads(content,
                      cls=cls, object_hook=object_hook,
                      parse_float=parse_float, parse_int=parse_int,
                      parse_constant=parse_constant,
                      object_pairs_hook=object_pairs_hook, **kw)


def loads(string, *, encoding=None, cls=None, object_hook=None, parse_float=None,
          parse_int=None, parse_constant=None, object_pairs_hook=None, **kw):
    root = os.path.abspath(os.path.curdir)
    string = _replace_import(string, root)
    string = _remove_comment(string)
    string = _fix_trailing_commas(string)
    return json.loads(string, encoding=encoding,
                      cls=cls, object_hook=object_hook,
                      parse_float=parse_float, parse_int=parse_int,
                      parse_constant=parse_constant,
                      object_pairs_hook=object_pairs_hook, **kw)


def _read_file(path):
    root = os.path.dirname(os.path.abspath(path))
    with open(path, 'r', encoding='utf8') as fd:
        content = fd.read()
    content = _replace_import(content, root)
    return content


def _replace_import(string, root):
    def include(match):
        m = match.group(1).strip()
        path = os.path.normpath(os.path.abspath(os.path.join(root, m)))
        if not os.path.exists(path):
            raise OSError("file %s not exists" % path)
        if not os.path.isfile(path):
            raise OSError("path %s is not a file" % path)
        content = _read_file(path)
        return content

    string = IMPORT_RE.sub(include, string)
    return string


def _remove_comment(string):
    def uncomment(match):
        s = match.group(0)
        if s[0] == '/':
            return ''
        return s

    string = COMMENTS_RE.sub(uncomment, string)
    return string


def _fix_trailing_commas(string):
    # Fix objects {} first.
    string = TRAILING_OBJECT_COMMAS_RE.sub("}", string)
    # Now fix arrays/lists [].
    string = TRAILING_ARRAY_COMMAS_RE.sub("]", string)
    return string
