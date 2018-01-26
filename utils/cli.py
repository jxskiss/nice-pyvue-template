# -*- coding:utf-8 -*-
"""
Candy utility to define and parse CLI arguments, inspired by the bin/cli
module from Apache Airflow (incubator) project.

This module is designed for small and medium command line application usage,
distributed (in different files) args and sub-commands definition are supported.
For simple use case without needs for sub-command, tornado.options
module is recommended if you are already using tornado.
If you are writing a large complicate application, google's open source
library abseil-py will give you much more help than this :-)
"""

from __future__ import absolute_import, print_function
from collections import namedtuple
import argparse


Arg = namedtuple(
    'Arg', ['flags', 'help', 'action', 'default', 'nargs', 'type', 'choices', 'metavar'])
Arg.__new__.__defaults__ = (None, ) * 7


class CLI(object):
    args = {}
    flags = set()
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
        if cls.flags & set(flags):
            raise ValueError('flags %r has already been used' % flags)
        cls.flags.update(flags)

        cls.args[arg] = Arg(flags, help, action, default, nargs, type, choices, metavar)
        return arg

    @classmethod
    def subcommand(cls, help, args):
        def decorator(func):
            cls.subparsers.append({
                'func': func,
                'help': help,
                'args': tuple(args)
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
            sub = subparsers_dict[sub]
            sp = subparsers.add_parser(sub['func'].__name__, help=sub['help'])
            for arg in sub['args']:
                arg = cls.args[arg]
                kwargs = {
                    f: getattr(arg, f)
                    for f in arg._fields if f != 'flags' and getattr(arg, f)
                }
                sp.add_argument(*arg.flags, **kwargs)
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

    # NOTE: the argument sub defined below is no difference with others
    # defined above, argument can be referenced by any sub-command
    # no matter where is it defined.
    # Arguments shared by multiple sub-commands should be defined globally.
    @subcommand(help='example sub-command',
                args=('some_id', 'text',
                      arg('sub', help='arg defined with subcommand')))
    def example(args):
        print('some_id:', args.some_id)
        print('text:', args.text)
        print('sub:', args.sub)

    run()
