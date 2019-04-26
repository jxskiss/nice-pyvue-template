from __future__ import unicode_literals

from django.db import models
from django.utils.translation import gettext_lazy as _


class TinyIntegerField(models.SmallIntegerField):
    description = _("Tiny integer")

    def db_type(self, connection):
        if connection.settings_dict['ENGINE'] == 'django.db.backends.mysql':
            return "tinyint"
        else:
            return super(TinyIntegerField, self).db_type(connection)


class PositiveTinyIntegerField(models.PositiveSmallIntegerField):
    description = _("Positive tiny integer")

    def db_type(self, connection):
        if connection.settings_dict['ENGINE'] == 'django.db.backends.mysql':
            return "tinyint UNSIGNED"
        else:
            return super(PositiveTinyIntegerField, self).db_type(connection)


class PositiveBigIntegerField(models.BigIntegerField):
    empty_strings_allowed = False
    description = _("Positive big (8 byte) integer")

    def db_type(self, connection):
        """
        Returns MySQL-specific column data type. Make additional checks
        to support other backends.
        """
        if connection.settings_dict['ENGINE'] == 'django.db.backends.mysql':
            return 'bigint UNSIGNED'
        return super(PositiveBigIntegerField, self).db_type(connection)

    def formfield(self, **kwargs):
        defaults = {'min_value': 0,
                    'max_value': models.BigIntegerField.MAX_BIGINT * 2 - 1}
        defaults.update(kwargs)
        return super(PositiveBigIntegerField, self).formfield(**defaults)


class PositiveBigAutoField(models.BigAutoField):
    description = _("Positive big (8 byte) integer")

    def db_type(self, connection):
        if connection.settings_dict['ENGINE'] == 'django.db.backends.mysql':
            return "bigint UNSIGNED AUTO_INCREMENT"
        else:
            return super(PositiveBigAutoField, self).db_type(connection)


class SizedTextField(models.TextField):
    description = _("Sized text")

    def __init__(self, *args, **kwargs):
        self.size_prefix = kwargs.pop('size_prefix', '')
        super(SizedTextField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(SizedTextField, self).deconstruct()
        if self.size_prefix != "":
            kwargs['size_prefix'] = self.size_prefix
        return name, path, args, kwargs

    def db_type(self, connection):
        if connection.settings_dict['ENGINE'] == 'django.db.backends.mysql':
            # tinytext, mediumtext, text, longtext
            return self.size_prefix + 'text'
        else:
            return super(SizedTextField, self).db_type(connection)


class SizedBinaryField(models.BinaryField):
    description = _("Sized binary")

    def __init__(self, *args, **kwargs):
        self.size_prefix = kwargs.pop('size_prefix', '')
        super(SizedBinaryField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(SizedBinaryField, self).deconstruct()
        if self.size_prefix != "":
            kwargs['size_prefix'] = self.size_prefix
        return name, path, args, kwargs

    def db_type(self, connection):
        if connection.settings_dict['ENGINE'] == 'django.db.backends.mysql':
            # tinyblob, mediumblob, blob, longblob
            return self.size_prefix + 'blob'
        else:
            return super(SizedBinaryField, self).db_type(connection)


class SizedDateTimeField(models.DateTimeField):
    description = _("Sized datetime")

    def __init__(self, *args, **kwargs):
        self.digit_num = kwargs.pop('digit_num', 0)
        super(SizedDateTimeField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(SizedDateTimeField, self).deconstruct()
        if self.digit_num != 0:
            kwargs['digit_num'] = self.digit_num
        return name, path, args, kwargs

    def db_type(self, connection):
        if connection.settings_dict['ENGINE'] == 'django.db.backends.mysql':
            digit_suffix = ''
            if self.digit_num > 0:
                digit_suffix = '(%d)' % self.digit_num
            return 'datetime' + digit_suffix
        else:
            return super(SizedDateTimeField, self).db_type(connection)
