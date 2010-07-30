import zope.schema
from zope.interface import Interface

SA_ECHO = True

#primitiveVocab = zope.schema.vocabulary.SimpleVocabulary.fromItems(items)
complexVocab = None

class IObject(Interface):
    """
    OBJECT SCHEMAZ
    """
    foo = zope.schema.TextLine(title=u"FOO")
    
class IDummy(Interface):
    """
    This is a dummy schema to test if the schema manger can properly import it.
    """
    
    integer = zope.schema.Int(
        title=u"INTEGER", 
        description=u"INTEGERDESC"
        )
    
    string = zope.schema.TextLine(
        title=u"STRING", 
        description=u"STRINGDESC"
        )
    
    boolean = zope.schema.Bool(
        title=u"BOOL", 
        description=u"BOOLDESC"
        )
    
    decimal = zope.schema.Decimal(
        title=u"DECIMAL", 
        description=u"DECIMALDESC"
        )
    
    date = zope.schema.Date(
        title=u"DATE", 
        description=u"DATE"
        )
    
    object = zope.schema.Object(
        title=u"OBJECT", 
        description=u"OBJECTDESC", 
        schema=IObject
        )
    
    list = zope.schema.List(
        title=u"LIST", 
        description=u"LIST", 
        value_type=zope.schema.Choice(
            title=u"LISTCHOICE", 
            values=('foo', 'bar', 'go' 'away', 'plz',))
        )
