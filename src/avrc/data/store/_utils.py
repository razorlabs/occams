"""
Library tools.
"""

import zope.schema
from zope.schema.vocabulary import SimpleVocabulary

_US_STATES_LIST = ["ca", "wa"]
statesVocabulary = SimpleVocabulary.fromValues(_US_STATES_LIST)


#
# TODO this really need to be replaced with something much cleaner
#
TYPE_2_STR = {
    zope.schema.Int: u"integer",
    zope.schema.TextLine: u"string",
    zope.schema.Bytes: u"binary",
    zope.schema.Bool: u"boolean",
    zope.schema.Decimal: u"real",
    zope.schema.Date: u"datetime",
    zope.schema.Object: u"object",
    }

STR_2_TYPE = dict(zip(TYPE_2_STR.values() ,TYPE_2_STR.keys()))