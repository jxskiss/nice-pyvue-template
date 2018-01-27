from peewee import (
    BooleanField, CharField, TextField, DateTimeField
)
import base64
import datetime
import hashlib
import json
import os
import threading


def fast_urandom16(urandom=[], lock=threading.RLock()):
    """
    This is 4x faster than calling os.urandom(16) and prevents
    the "too many files open" issue with concurrent access to os.urandom()
    """
    try:
        return urandom.pop()
    except IndexError:
        try:
            lock.acquire()
            ur = os.urandom(16 * 1024)
            urandom.extend(ur[i:i + 16] for i in range(16, 1024 * 16, 16))
            return ur[0:16]
        finally:
            lock.release()


def make_salt(size=16):
    if size == 16:
        return fast_urandom16().hex()
    return os.urandom(size).hex()


class AbstractUser(object):
    """
    General purpose user model with asynchronous methods.

    Subclass must define peewee's "Meta" class and "manager" class attribute,
    which is peewee_async's Manager object.

    This model is mainly borrowed from uvtor and django.
    """
    date_joined = DateTimeField(default=datetime.datetime.now)
    username = CharField(unique=True)
    password = CharField()
    salt = CharField(default=make_salt)
    email = CharField(default='')
    phone = CharField(default='')
    first_name = CharField(default='')
    last_name = CharField(default='')
    is_active = BooleanField(default=True)
    is_staff = BooleanField(default=False)
    is_superuser = BooleanField(default=False)
    last_login = DateTimeField(null=True)

    def __str__(self):
        return '%s' % self.username

    @staticmethod
    def get_password(raw_password, salt, iterations=24000):
        hash = base64.b64encode(
            hashlib.pbkdf2_hmac('sha256',
                                raw_password.encode('utf8'),
                                salt.encode('utf8'),
                                iterations)
        ).decode()
        password = 'pbkdf2_sha256${}${}'.format(iterations, hash)
        return password

    def check_password(self, raw_password):
        iterations, truth = self.password.split('$')[1:]
        password = self.get_password(raw_password, self.salt, iterations)
        return password == truth

    async def set_password(self, raw_password):
        update_fields = ['password']
        if not self.salt:
            self.salt = make_salt()
            update_fields.append('salt')
        self.password = self.get_password(raw_password, self.salt)
        await self.manager.update(self, only=update_fields)

    @classmethod
    async def create_user(cls, username, password,
                          email='', phone='', first_name='', last_name='',
                          is_staff=False, is_superuser=False):
        salt = make_salt()
        password = cls.get_password(password, salt)
        params = {
            'username': username,
            'password': password,
            'salt': salt,
            'email': email,
            'phone': phone,
            'first_name': first_name,
            'last_name': last_name,
            'is_staff': is_staff,
            'is_superuser': is_superuser
        }
        return await cls.manager.create(cls, **params)


class AbstractKVStore(object):
    """
    General purpose KV store model with asynchronous class methods.

    Subclass must define peewee's "Meta" class and "manager" class attribute,
    which is peewee_async's Manager object.
    """
    k = CharField(verbose_name='Key', max_length=255, unique=True)
    v = TextField(verbose_name='Value', default='')
    create_at = DateTimeField(default=datetime.datetime.now)
    update_at = DateTimeField(default=datetime.datetime.now)
    expire_at = DateTimeField(null=True)

    def __str__(self):
        return '%s' % self.k

    @classmethod
    async def get(cls, key, default=None):
        try:
            obj = await cls.manager.get(cls, k=key)
            if obj.expire_at and obj.expire_at < datetime.datetime.now():
                return default
            return obj.v
        except cls.DoesNotExist:
            return default

    @classmethod
    async def get_json(cls, key, default=None):
        value = await cls.get(key, default=default)
        if value is not default:
            value = json.loads(value)
        return value

    @classmethod
    async def set(cls, key, value, expire_at=None):
        obj, is_created = await cls.manager.create_or_get(
            cls, k=key, v=value, expire_at=expire_at)
        if not is_created:
            obj.value = value
            obj.update_at = datetime.datetime.now()
            obj.expire_at = expire_at
            await cls.manager.update(
                obj, only=('value', 'update_at', 'expire_at')
            )
        return True

    @classmethod
    async def set_json(cls, key, value, expire_at=None):
        value = json.dumps(value)
        return await cls.set(key, value, expire_at=expire_at)

    @classmethod
    async def del_key(cls, key):
        try:
            obj = await cls.manager.get(cls, k=key)
            await cls.manager.delete(obj)
            return obj.v
        except cls.DoesNotExist:
            return None
