"""
Library tools.
"""
from zope.component import adapts, getUtility
from zope.interface import implements

from avrc.data.store import interfaces
from avrc.data.store import _model

class SubjectName(object):
    implements(interfaces.ISubject)
    adapts(interfaces.ISubject)
    
    def __init__(self, context):
        self.context = context
        self.props = {}
        
        Session = getUtility(interfaces.ISessionFactory)
        Session()
        
        name = Session.query(_model.Name)\
               .filter_by(ourid=self.context.number)\
               .last()

        if name is not None:               
            self.first = name.first
            self.middle = name.middle
            self.last = name.last
            self.sur = name.sur
