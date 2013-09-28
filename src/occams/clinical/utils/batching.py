from math import ceil


class Batch(object):
    """
    A no-frills paginator
    """

    @property
    def page_count(self):
        return int(ceil(self.total / float(self.per_page)))

    @property
    def has_previous(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.page_count

    def __init__(self, iterable, total, page=1, per_page=20):
        self.iterable
        self.total
        self.page = page
        self.per_page = per_page

    def pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
        last = 0
        for i in xrange(1, self.pages_count + 1):
            if (i <= left_edge
                    or (i > self.page - left_current - 1 and  i < self.page + right_current)
                    or i > self.pages - right_edge):
                if last + 1 != i:
                    yield None
                yield i
                last = i

    def items(self):
        return self.iterable

