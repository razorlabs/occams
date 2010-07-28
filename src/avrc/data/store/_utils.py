"""
Library tools.
"""
from zope.component import adapts, getUtility
from zope.interface import implements


from avrc.data.store import interfaces
from avrc.data.store import model

from zope.schema.vocabulary import SimpleVocabulary

_US_STATES_LIST = ["ca", "wa"]
statesVocabulary = SimpleVocabulary.fromValues(_US_STATES_LIST)


import zope.schema
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



class SubjectName(object):
    implements(interfaces.ISubject)
    adapts(interfaces.ISubject)
    
    def __init__(self, context):
        self.context = context
        self.props = {}
        
        Session = getUtility(interfaces.ISessionFactory)
        Session()
        
        name = Session.query(model.Name)\
               .filter_by(ourid=self.context.number)\
               .last()

        if name is not None:               
            self.first = name.first
            self.middle = name.middle
            self.last = name.last
            self.sur = name.sur
