# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function
from six import b
import hashlib
import json
import os
import shutil
import unittest

from utils.decorators import file_cached_property


class FileCached(object):

    @file_cached_property
    def prop(self):
        return 'dummy'

    @file_cached_property(key='keyed')
    def another(self):
        return 'keyed'

    @file_cached_property
    def unique(self):
        return id(self)


class FileCachedPropertyTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)

    @property
    def cache_dir(self):
        return '_test_cache'

    def test_cache_keys(self):
        _file = os.path.join(self.cache_dir, 'keys.json')
        obj1 = FileCached()
        obj1.property_cache_file = _file
        self.assertFalse(os.path.exists(_file))

        self.assertEqual(obj1.prop, 'dummy')
        self.assertTrue(os.path.exists(_file))
        self.assertEqual(obj1.another, 'keyed')
        with open(_file, 'r') as fd:
            cache = json.load(fd)
        self.assertTrue('prop' in cache)
        self.assertTrue(cache['prop'][0] == 'dummy')
        self.assertIsInstance(cache['prop'][1], float)
        self.assertTrue('keyed' in cache)
        self.assertTrue(cache['keyed'][0] == 'keyed')

    def test_different_objs(self):
        _file1 = os.path.join(self.cache_dir, 'obj1.json')
        obj1 = FileCached()
        obj1.property_cache_file = _file1

        _file2 = os.path.join(self.cache_dir, 'obj2.json')
        obj2 = FileCached()
        obj2.property_cache_file = _file2

        shared1 = file_cached_property.shared_name(obj1.property_cache_file)
        shared2 = file_cached_property.shared_name(obj2.property_cache_file)

        self.assertEqual(obj1.prop, obj2.prop)
        self.assertTrue(hasattr(obj1, '_file_cached'))
        self.assertTrue(hasattr(obj2, '_file_cached'))
        self.assertIsNot(obj1._file_cached, obj2._file_cached)
        self.assertTrue(hasattr(file_cached_property, shared1))
        self.assertTrue(hasattr(file_cached_property, shared2))


if __name__ == '__main__':
    unittest.main()
