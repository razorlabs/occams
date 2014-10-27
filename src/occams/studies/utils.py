from math import ceil


class Pagination(object):
    """
    Pagination helper
    http://flask.pocoo.org/snippets/44/
    """

    def __init__(self, page, per_page, total_count):
        self.per_page = per_page
        self.total_count = total_count
        self.page = max(1, min(page, self.pages))

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def offset(self):
        return (self.page - 1) * self.per_page

    @property
    def is_first(self):
        return self.page == 1

    @property
    def is_last(self):
        return self.page == self.pages

    @property
    def has_previous(self):
        return self.page > 1

    @property
    def previous_page(self):
        return max(1, self.page - 1)

    @property
    def has_next(self):
        return self.page < self.pages

    @property
    def next_page(self):
        return min(self.page + 1, self.pages)

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num
