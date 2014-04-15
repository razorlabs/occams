from __future__ import division
from math import ceil

from six.moves import range
from pyramid.renderers import render


class Pager(object):
    """
    Helper component for calculation pagination values

    Taken from:
        http://flask.pocoo.org/snippets/44/
    """

    def __init__(self, page, per_page, total_count):
        try:
            page = int(page)
        except ValueError:
            page = 1

        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        return int(ceil(self.total_count / self.per_page))

    @property
    def has_previous(self):
        return self.page > 1

    @property
    def previous(self):
        return self.page - 1 if self.has_previous else self.page

    @property
    def has_next(self):
        return self.page < self.pages

    @property
    def next(self):
        return self.page + 1 if self.has_next else self.page

    @property
    def slice_start(self):
        return (self.page - 1) * self.per_page

    @property
    def slice_end(self):
        return self.slice_start + self.per_page

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        last = 0
        for num in range(1, self.pages + 1):
            if (num <= left_edge
                    or (num > self.page - left_current - 1
                        and num < self.page + right_current)
                    or num > self.pages - right_edge):
                if last + 1 != num:
                    yield None
                yield num
                last = num

    def render(self, template,  url=None,
               left_edge=2, left_current=2,
               right_current=5, right_edge=2):
        return render(template, {
            'url': url or (lambda p: '#'),
            'pager': self,
            'pages': self.iter_pages(left_edge, left_current,
                                     right_current, right_edge)})

    def serialize(self):
        return {
            'page': self.page,
            'per_page': self.per_page,
            'total_count': self.total_count,
            'pages': self.pages,
            'has_previous': self.has_previous,
            'previous': self.previous,
            'has_next': self.has_next,
            'next': self.next}
