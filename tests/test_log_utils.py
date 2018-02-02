from __future__ import absolute_import, print_function, unicode_literals
import unittest
import logging
import sys

from utils.log import *

logging.basicConfig(level=logging.INFO)


class StreamLogWriterTest(unittest.TestCase, LoggerMixin):

    def setUp(self):
        self.log_file = 'test.log'
        self.handler = logging.FileHandler(self.log_file)
        self.log.addHandler(self.handler)

    def tearDown(self):
        import os
        self.log.removeHandler(self.handler)
        self.handler.close()
        os.remove(self.log_file)

    def test_log_attribute(self):
        self.assertIsInstance(self.log, logging.Logger)

    def test_log_stdout(self):
        with log_stdout(self.log, logging.INFO):
            print('test_log_stdout')

        with open(self.log_file, 'r') as fd:
            out = fd.read()
        self.assertIn('test_log_stdout', out)

        # there should be only one newline character
        # self.assertEqual(content, 'test_log_stdout\n')

    def test_log_stderr(self):
        with log_stderr(self.log, logging.ERROR):
            sys.stderr.write('test_log_stderr')

        with open(self.log_file, 'r') as fd:
            out = fd.read()

        self.assertIn('test_log_stderr', out)

    def test_log_must_be_flushed(self):
        with log_stdout(self.log, logging.INFO):
            print('first line')

        with open(self.log_file, 'r') as fd:
            out = fd.read()
        self.assertEqual(out, 'first line\n')

        with log_stdout(self.log, logging.INFO):
            sys.stdout.write('second line')

        with open(self.log_file, 'r') as fd:
            out = fd.read()
        self.assertEqual(out, 'first line\nsecond line\n')

    def test_print_should_be_on_same_line(self):
        with log_stdout(self.log, logging.INFO):
            print('first', 'second')

        with open(self.log_file, 'r') as fd:
            out = fd.read()
        self.assertEqual(out, 'first second\n')
