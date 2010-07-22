
from zope.schema.vocabulary import SimpleVocabulary

US_STATES_LIST = ["ca", "wa"]

statesVocabulary = SimpleVocabulary.fromValues(US_STATES_LIST)

TYPES = (
    ('binary',),
    ('boolean',),
    ('datetime',),
    ('date'),
    ('time'),
    ('integer',),
    ('real',),
    ('string',),
    ('text',),
    ('object',),
    )