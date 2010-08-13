import zope.schema
from zope.interface import Interface
from plone.directives import form

class ISimple(Interface):
    """
    OBJECT SCHEMAZ
    """
    foo = zope.schema.TextLine(title=u"FOO")

class IStandaloneInterface(Interface):
    """
    This is very simple stanalone interface.
    """

    foo = zope.schema.TextLine(
        title=u"Foo",
        description=u"Something about foo.",
        required=True
        )

    bar = zope.schema.Text(
        title=u"Bar",
        description=u"Something about bar."
        )

    baz = zope.schema.Int(
        title=u"Baz",
        description=u"Something about baz."
        )

class IComposedInterface(Interface):
    """
    This class contains annotations which SHOULD be saved as well...
    """

    integer = zope.schema.Int(
        title=u"INTEGER",
        description=u"INTEGERDESC"
        )

    object = zope.schema.Object(
        title=u"OBJECT",
        description=u"OBJECTDESC",
        schema=ISimple
        )

class IAnnotatedInterface(Interface):
    """
    This is a dummy schema to test if the schema manger can properly import it.
    Also this class contains annotations which SHOULD be saved as well...
    """

    form.mode(integer='hidden')
    integer = zope.schema.Int(
        title=u"INTEGER",
        description=u"INTEGERDESC"
        )

    form.omitted('integer')
    ommitme = zope.schema.Int(
        title=u"OMITME",
        description=u"PLEASE"
        )

    form.read_permission(list="zope2.View")
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
    form.write_permission(date="cmf.ModifyPortalContent")
    date = zope.schema.Date(
        title=u"DATE",
        description=u"DATE"
        )

class IChoicedInterface(Interface):
    """
    This simply tests that a vocabulary
    """

    choice = zope.schema.Choice(
            title=u"LISTCHOICE",
            values=('foo', 'bar', 'go' 'away', 'plz',)
        )

