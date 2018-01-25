# -*- coding:utf-8 -*-
"""
Candy utility to define and parse CLI arguments, borrowed from
Apache Airflow's bin/cli module.
"""

from __future__ import absolute_import, print_function
from collections import namedtuple
import argparse


Arg = namedtuple(
    'Arg', ['flags', 'help', 'action', 'default', 'nargs', 'type', 'choices', 'metavar'])
Arg.__new__.__defaults__ = (None, ) * 7


class CLI(object):
    args = {}
    subparsers = []

    @classmethod
    def arg(cls, arg, flags=None, help=None, action=None, default=None, nargs=None,
            type=None, choices=None, metavar=None):
        """See argparse for parameters document."""
        if flags is None:
            flags = ('--%s' % arg, )
        elif isinstance(flags, str):
            flags = (flags, )
        cls.args[arg] = Arg(flags, help, action, default, nargs, type, choices, metavar)

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


get_parser = CLI.get_parser


if __name__ == '__main__':
    CLI.arg('some_id', type=int, help='example int id argument')
    CLI.arg('text', help='example text argument')

    @CLI.subcommand(help='example sub-command', args=('some_id', 'text'))
    def example(args):
        print('some_id:', args.some_id)
        print('text:', args.text)

    parser = get_parser()
    args = parser.parse_args()
    args.func(args)
