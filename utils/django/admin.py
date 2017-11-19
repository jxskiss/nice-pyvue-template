# -*- coding:utf-8 -*-
from django.contrib import admin, auth
from django.utils import timezone
import json

__all__ = [
    'create_modeladmin',
    'make_related_field', 'make_json_field',
    'LastWeekDateFilter', 'make_last_week_date_filter',
    'IsNullOrNotFilter', 'make_isnull_or_not_filter',
    'FKUserFilter', 'make_fk_user_filter',
]


def create_modeladmin(model, model_admin, name=None,
                      verbose_name=None, verbose_name_plural=None):
    """
    Create proxy admin model dynamically.
    """
    _verbose_name = verbose_name
    _verbose_name_plural = verbose_name_plural or verbose_name

    class Meta:
        proxy = True
        app_label = model._meta.app_label
        if _verbose_name:
            verbose_name = _verbose_name
        if _verbose_name_plural:
            verbose_name_plural = _verbose_name_plural

    attrs = {'__module__': '', 'Meta': Meta}
    new_model = type(name, (model,), attrs)

    admin.site.register(new_model, model_admin)


def make_related_field(model, field, related_field):
    """
    Create related foreign field dynamically.
    """
    def field_function(self, obj):
        return getattr(getattr(obj, field), related_field)

    field_function.short_description = model._meta.get_field(
        related_field).verbose_name
    field_function.admin_order_field = '{}__{}'.format(
        model._meta.model_name, related_field)
    return field_function


def make_json_field(field, short_description):
    """
    Create pre formatted json field.
    """
    def field_function(self, obj):
        value = getattr(obj, field)
        if value is None:
            return '--'
        return '<div><br><pre>{}</pre></div>'.format(
            json.dumps(value, indent=4, ensure_ascii=False)
        )

    field_function.allow_tags = True
    field_function.short_description = short_description
    return field_function


class LastWeekDateFilter(admin.SimpleListFilter):
    title = ''
    parameter_name = ''
    template = 'common/admin/dropdown_filter.html'
    date_field = ''

    def lookups(self, request, model_admin):
        today = timezone.now().date()
        lookups = []
        for x in range(7):
            date = (today - timezone.timedelta(days=x)).strftime('%Y-%m-%d')
            lookups.append((date, date))
        return lookups

    def queryset(self, request, queryset):
        date_str = self.value()
        if date_str:
            date = timezone.datetime(
                *map(int, date_str.split('-')),
                tzinfo=timezone.get_current_timezone())
            queryset = queryset.filter(**{
                self.date_field + '__gte': date,
                self.date_field + '__lt': date + timezone.timedelta(days=1)
            })
        return queryset


def make_last_week_date_filter(field, title=None, parameter_name=None,
                               template='common/admin/dropdown_filter.html'):
    """
    Create date filter in last week for given field.
    """
    _title = title or '{} Date'.format(field.title())
    _parameter_name = parameter_name or '{}_last_week_data'.format(field)
    _template = template

    class _ThisLastWeekDateFilter(LastWeekDateFilter):
        title = _title
        parameter_name = _parameter_name
        template = _template
        date_field = field

    return _ThisLastWeekDateFilter


class IsNullOrNotFilter(admin.SimpleListFilter):
    title = ''
    parameter_name = ''
    nullable_field = ''

    def lookups(self, request, model_admin):
        return [
            ('1', 'Is Null'),
            ('0', 'Not Null'),
        ]

    def queryset(self, request, queryset):
        param = self.value()
        if param:
            isnull = bool(int(param))
            queryset = queryset.filter(**{
                self.nullable_field + '__isnull': isnull
            })
        return queryset


def make_isnull_or_not_filter(field, title=None, parameter_name=None):
    """
    Create is null or not filter for given field.
    """
    _title = title or '{} Is Null'.format(field.title())
    _parameter_name = parameter_name or '{}_isnull'.format(field)

    class _ThisIsNullOrNotFilter(IsNullOrNotFilter):
        title = _title
        parameter_name = _parameter_name
        nullable_field = field

    return _ThisIsNullOrNotFilter


class FKUserFilter(admin.SimpleListFilter):
    title = ''
    parameter_name = ''
    template = 'common/admin/dropdown_filter.html'
    user_field = ''

    def lookups(self, request, model_admin):
        user_model = auth.get_user_model()
        users = user_model.objects.all().order_by('pk')
        return [
            (u.id, u.username)
            for u in users
        ]

    def queryset(self, request, queryset):
        user_id = self.value()
        if user_id:
            queryset = queryset.filter(**{
                self.user_field + '_id': int(user_id)
            })
        return queryset


def make_fk_user_filter(field, title=None, parameter_name=None,
                        template='common/admin/dropdown_filter.html'):
    """
    Create related foreign key user filter.
    """
    _title = title or '{} User'.format(field.title())
    _parameter_name = parameter_name or '{}_id__exact'.format(field)
    _template = template

    class _ThisFKUserFilter(FKUserFilter):
        title = _title
        parameter_name = _parameter_name
        template = _template
        user_field = field

    return _ThisFKUserFilter
