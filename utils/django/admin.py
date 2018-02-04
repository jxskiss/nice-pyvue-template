# -*- coding:utf-8 -*-
from django.contrib import admin, auth
from django.utils import timezone
import json

__all__ = [
    'DropdownFilter', 'DropdownRelatedFilter', 'DropdownChoicesFilter',
    'create_modeladmin',
    'make_related_field', 'make_json_field',
    'LastDaysFilter', 'make_last_days_filter',
    'IsNullOrNotFilter', 'make_isnull_or_not_filter',
    'NullableBooleanFilter', 'make_nullable_boolean_filter',
    'FKUserFilter', 'make_fk_user_filter',
    'RangeValueFilter', 'make_range_value_filter',
]


class DropdownFilter(admin.AllValuesFieldListFilter):
    template = 'common/admin/dropdown_filter.html'


class DropdownRelatedFilter(admin.RelatedFieldListFilter):
    template = 'common/admin/dropdown_filter.html'


class DropdownChoicesFilter(admin.ChoicesFieldListFilter):
    template = 'common/admin/dropdown_filter.html'


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


class LastDaysFilter(admin.SimpleListFilter):
    title = ''
    parameter_name = ''
    date_field = ''
    days_count = 7
    template = 'common/admin/dropdown_filter.html'

    def lookups(self, request, model_admin):
        today = timezone.now().date()
        lookups = []
        for x in range(self.days_count):
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


def make_last_days_filter(field, days=7,
                          title=None, parameter_name=None,
                          template='common/admin/dropdown_filter.html'):
    """
    Create date filter in last week for given field.
    """
    _title = title or '{} Date'.format(field.title())
    _parameter_name = parameter_name or '{}_date'.format(field)
    _template = template

    class _TheLastDaysFilter(LastDaysFilter):
        title = _title
        parameter_name = _parameter_name
        template = _template
        date_field = field
        days_count = days

    return _TheLastDaysFilter


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

    class _TheIsNullOrNotFilter(IsNullOrNotFilter):
        title = _title
        parameter_name = _parameter_name
        nullable_field = field

    return _TheIsNullOrNotFilter


class NullableBooleanFilter(admin.SimpleListFilter):
    title = ''
    parameter_name = ''
    boolean_field = ''

    def lookups(self, request, model_admin):
        return [
            ('all', 'All'),
            ('yes', 'Yes'),
            ('no', 'No'),
            ('null', 'Unknown'),
        ]

    def queryset(self, request, queryset):
        f = self.value()
        if f == 'yes':
            return queryset.filter(**{self.boolean_field: True})
        elif f == 'no':
            return queryset.filter(**{self.boolean_field: False})
        elif f == 'null':
            return queryset.filter(**{self.boolean_field + '__isnull': True})
        return queryset

    def choices(self, changelist):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': changelist.get_query_string(
                    {self.parameter_name: lookup}, []),
                'display': title,
            }


def make_nullable_boolean_filter(field, title=None, parameter_name=None):
    _title = title or field.title()
    _parameter_name = parameter_name or field

    class _TheNullableBooleanFilter(NullableBooleanFilter):
        title = _title
        parameter_name = _parameter_name
        boolean_field = field

    return _TheNullableBooleanFilter


class FKUserFilter(admin.SimpleListFilter):
    title = ''
    parameter_name = ''
    user_field = ''
    template = 'common/admin/dropdown_filter.html'

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

    class _TheFKUserFilter(FKUserFilter):
        title = _title
        parameter_name = _parameter_name
        template = _template
        user_field = field

    return _TheFKUserFilter


class RangeValueFilter(admin.SimpleListFilter):
    title = ''
    parameter_name = ''
    value_field = ''
    value_ranges = ()
    template = 'common/admin/dropdown_filter.html'

    def lookups(self, request, model_admin):
        if not self.value_ranges:
            return []
        result = [('0', '< %s' % self.value_ranges[0][0])]
        for idx, r in enumerate(self.value_ranges):
            result.append((str(idx + 1), '[{} - {})'.format(*r)))
        result.append(
            (str(len(self.value_ranges) + 1),
             '>= %s' % self.value_ranges[-1][1]))
        return result

    def queryset(self, request, queryset):
        if not self.value_ranges:
            return queryset
        value = self.value
        if int(value) <= 0:
            return queryset.filter(**{
                self.value_field + '__lt': self.value_ranges[0][0]
            })
        elif int(value) > len(self.value_ranges):
            return queryset.filter(**{
                self.value_field + '__gte': self.value_ranges[-1][1]
            })
        else:
            r = self.value_ranges[int(value)-1]
            return queryset.filter(**{
                self.value_field + '__gte': r[0],
                self.value_field + '__lt': r[1]
            })


def make_range_value_filter(field, title=None, parameter_name=None,
                            value_ranges=None,
                            template='common/admin/dropdown_filter.html'):
    _title = title or '{} Ranges'.format(field.title())
    _parameter_name = parameter_name or '{}_range'.format(field)
    _value_ranges = sorted(value_ranges)
    _template = template

    class _TheRangeValueFilter(RangeValueFilter):
        title = _title,
        parameter_name = _parameter_name
        value_ranges = _value_ranges
        template = _template

    return _TheRangeValueFilter
