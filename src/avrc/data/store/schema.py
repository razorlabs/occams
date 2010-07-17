"""
"""

import zope.schema
from zope.interface import implements
from zope.interface.interface import InterfaceClass
from zope.component import adapts

from avrc.data.store import interfaces


# Test dynamic schema
DynamicInterface = InterfaceClass('DynamicInterface', attrs=dict(
    size=zope.schema.TextLine(title=u"size")
    ))

class DummySchema(object):
    pass

class DummyField(object):
    pass

class SchemaManager(object):
    """
    """
    implements(interfaces.ISchemaManager)
    
    
    def __init__(self):
        """
        """
    
    
    def add(self, name):
        """
        """
        raise NotImplementedError()
        
        
    def importSchema(self, schema):
        """
        """
        myschema = DummySchema()
        
        for name, type in zope.schema.getFieldsInOrder(schema):
            myfield = DummyField()
            myfield.title = getattr(type, 'title', None)
            myfield.description = getattr(type, 'description', None)
            
            
            setattr(myschema, name, myfield)
            print
            print name
            print 'min: ' + str(getattr(type, 'min', None))
            print

        
        raise NotImplementedError()
        
        
    def getSchema(self, protocol, title):
        """
        """
        raise NotImplementedError()
        
        
    

class SubjectData(object):
    """
    """
    implements(interfaces.IMutableSchema)
    adapts(interfaces.ISubject)
    
    
    

class MutableSchema(object):
    """
    """
