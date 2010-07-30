"""
Library tools.
"""

import zope.schema
from zope.schema.vocabulary import SimpleVocabulary

_US_STATES_LIST = ["ca", "wa"]
statesVocabulary = SimpleVocabulary.fromValues(_US_STATES_LIST)