# -*- coding:utf-8 -*-
"""
Candy utility to define and parse CLI arguments, inspired by the bin/cli
module from Apache Airflow (incubator) project.

This module is designed for small and medium command line application usage,
distributed (in different files) args and sub-commands definition are supported.

For simple use case without needs for sub-command, tornado.options
module is recommended if you are already using tornado.

If you are writing a large complicate application, google's open source
library abseil-py may give you much more help :-)
"""

from __future__ import absolute_import, print_function
from collections import namedtuple, defaultdict
import argparse


Arg = namedtuple(
    'Arg', ['flags', 'help', 'action', 'default', 'nargs', 'type', 'choices', 'metavar'])
Arg.__new__.__defaults__ = (None, ) * 7


class CLI(object):
    args = {}
    subargs = defaultdict(dict)
    subparsers = []

    @classmethod
    def arg(cls, arg, flags=None, help=None, action=None, default=None, nargs=None,
            type=None, choices=None, metavar=None):
        """See argparse for parameters document."""
        if arg in cls.args:
            raise ValueError('argument %r has already been defined' % arg)

        if flags is None:
            flags = ('--%s' % arg, )
        elif isinstance(flags, str):
            flags = (flags, )

        _A = Arg(flags, help, action, default, nargs, type, choices, metavar)
        cls.args[arg] = _A
        return arg, _A

    @classmethod
    def subcommand(cls, help, args):
        def decorator(func):
            string_args = []
            for arg in args:
                if isinstance(arg, tuple):
                    cls.subargs[func.__name__][arg[0]] = arg[1]
                    cls.args.pop(arg[0])
                    string_args.append(arg[0])
                else:
                    string_args.append(arg)

            cls.subparsers.append({
                'func': func,
                'help': help,
                'args': tuple(string_args)
            })
            return func
        return decorator

    @classmethod
    def get_parser(cls):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(
            help='sub-command help', dest='subcommand')
        subparsers.required = True

        subparsers_dict = {sp['func'].__name__: sp for sp in cls.subparsers}
        subparse_list = subparsers_dict.keys()
        for sub in subparse_list:
            name = sub
            sub = subparsers_dict[sub]
            sp = subparsers.add_parser(name, help=sub['help'])
            for arg in sub['args']:
                _A = cls.subargs[name].get(arg) or cls.args.get(arg)
                if not _A:
                    raise ValueError('argument %r is not defined' % arg)
                kwargs = {
                    f: getattr(_A, f)
                    for f in _A._fields if f != 'flags' and getattr(_A, f)
                }
                sp.add_argument(*_A.flags, **kwargs)
            sp.set_defaults(func=sub['func'])
        return parser

    @classmethod
    def run(cls):
        parser = cls.get_parser()
        args = parser.parse_args()
        args.func(args)


arg = CLI.arg
subcommand = CLI.subcommand
get_parser = CLI.get_parser
run = CLI.run


if __name__ == '__main__':
    arg('some_id', type=int, help='example int id argument')
    arg('text', help='example text argument')

    # Shared arguments should be defined globally, which can be referenced
    # by any sub-command, no matter where are they located.
    # While arguments defined with sub-command are owned by the sub-command
    # itself, which won't be seen by any other sub-command.

    @subcommand(help='example sub-command',
                args=('some_id', 'text',
                      arg('sub', help='sub arg defined with subcommand')))
    def example(args):
        print('some_id:', args.some_id)
        print('text:', args.text)
        print('sub:', args.sub)

    @subcommand(help='another sub-command',
                args=('some_id', 'text',
                      arg('sub', help='sub arg defined for another subcommand')))
    def another(args):
        print('some_id:', args.some_id)
        print('sub:', args.sub)

    run()
