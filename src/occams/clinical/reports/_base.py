class Report(object):

    name = None
    title = None
    has_private = False
    has_rand = False

    versions = []

    def codebook(self):
        raise NotImplemented

    def data(self):
        raise NotImplemented

    def to_json(self):
        keys = ('name', 'title', 'has_private', 'has_rand')
        ret = dict((k, getattr(self, k)) for k in keys)
        ret['versions'] = list(map(str, self.versions))
        return ret
