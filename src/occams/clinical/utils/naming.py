import re

RE_WS = re.compile('\s+')
RE_NON_ASCII = re.compile('[^a-z0-9_-]', re.I)


def tokenize(value):
    """ Converts the value into a vocabulary token value """
    return RE_NON_ASCII.sub('', RE_WS.sub('-', str(value).strip().lower()))
