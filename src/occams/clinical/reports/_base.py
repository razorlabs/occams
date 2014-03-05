class Report(object):

    name = None
    title = None
    has_private = False
    has_rand = False

    publications = []

    def codebook(self):
        raise NotImplemented

    def data(self):
        raise NotImplemented
