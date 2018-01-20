from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
import json

# Create your models here.


class AbstractKVStore(models.Model):
    k = models.CharField('Key', max_length=255, unique=True)
    v = models.TextField('Value', default='', blank=True)
    create_at = models.DateTimeField('Create at', auto_now_add=True)
    update_at = models.DateTimeField('Update at', auto_now=True)
    expire_at = models.DateTimeField('Expire at', null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return '%s' % self.k

    @classmethod
    def get(cls, key, default=None):
        try:
            obj = cls.objects.get(k=key)
            if obj.expire_at and obj.expire_at < timezone.now():
                return default
            return obj.v
        except cls.DoesNotExist:
            return default

    @classmethod
    def get_json(cls, key, default=None):
        value = cls.get(key, default=default)
        if value is not default:
            value = json.loads(value)
        return value

    @classmethod
    def set(cls, key, value, expire_at=None):
        obj, created = cls.objects.update_or_create(
            k=key, defaults={'v': value, 'expire_at': expire_at})
        return True

    @classmethod
    def set_json(cls, key, value, expire_at=None):
        value = json.dumps(value)
        return cls.set(key, value, expire_at=expire_at)

    @classmethod
    def del_key(cls, key):
        try:
            obj = cls.objects.get(k=key)
            obj.delete()
            return obj.v
        except cls.DoesNotExist:
            return None
