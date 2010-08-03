import zope.schema
from zope.interface import Interface
from plone.directives import form

SA_ECHO = True

class IObject(Interface):
    """
    OBJECT SCHEMAZ
    """
    foo = zope.schema.TextLine(title=u"FOO")

class IDummy(Interface):
    """
    This is a dummy schema to test if the schema manger can properly import it.
    """

    form.mode(integer='hidden')
    integer = zope.schema.Int(
        title=u"INTEGER",
        description=u"INTEGERDESC"
        )

    form.widget(text='plone.app.z3cform.wysiwyg.WysiwygFieldWidget',)
    text = zope.schema.Text(
        title=u"TEXT",
        description=u"TEXTDESC",
        )

    form.order_before(string='text')
    string = zope.schema.TextLine(
        title=u"STRING",
        description=u"STRINGDESC"
        )

    form.order_after(boolean="decimal")
    boolean = zope.schema.Bool(
        title=u"BOOL",
        description=u"BOOLDESC"
        )

    form.write_permission(decimal="cmf.ModifyPortalContent")
    decimal = zope.schema.Decimal(
        title=u"DECIMAL",
        description=u"DECIMALDESC"
        )

    form.mode(date='hidden')
    date = zope.schema.Date(
        title=u"DATE",
        description=u"DATE"
        )

    form.omitted('object')
    object = zope.schema.Object(
        title=u"OBJECT",
        description=u"OBJECTDESC",
        schema=IObject
        )

    form.read_permission(list="zope2.View")
    list = zope.schema.List(
        title=u"LIST",
        description=u"LIST",
        value_type=zope.schema.Choice(
            title=u"LISTCHOICE",
            values=('foo', 'bar', 'go' 'away', 'plz',))
        )
