# -*- coding:utf-8 -*-


class FilterClause(object):

    def __init__(self, clause=''):
        self.clause = clause

    def __and__(self, other):
        left = str(self).strip()
        right = str(other).strip()
        if all((left, right)):
            return FilterClause('(%s) AND (%s)' % (left, right))
        elif any((left, right)):
            return FilterClause(left or right)
        else:
            return FilterClause('')

    def __or__(self, other):
        left = str(self).strip()
        right = str(other).strip()
        if all((left, right)):
            return FilterClause('(%s) OR (%s)' % (left, right))
        elif any((left, right)):
            return FilterClause(left or right)
        else:
            return ''

    def __str__(self):
        return '%s' % self.clause
