import zope.schema
from zope.interface import Interface
from zope.interface import Attribute
from plone.directives import form
from avrc.data.store import Schema

class INotImportant(Interface):
    pass

class ISimple(Schema, INotImportant):
    """
    OBJECT SCHEMAZ
    """

class IStandaloneInterface(Schema):
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

class IDependentInterface(Schema):
    """
    as;dlfjasd;fjfasd;fsad
    """



setattr(IDependentInterface, "__dependents__", (ISimple, IStandaloneInterface,))

class IComposedInterface(Schema):
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

class IAnnotatedInterface(Schema):
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
    decimal = zope.schema.Float(
        title=u"DECIMAL",
        description=u"DECIMALDESC"
        )

    form.mode(date='hidden')
    form.write_permission(date="cmf.ModifyPortalContent")
    date = zope.schema.Date(
        title=u"DATE",
        description=u"DATE"
        )

class IChoicedInterface(Schema):
    """
    This simply tests that a vocabulary
    """

    choice = zope.schema.Choice(
            title=u"LISTCHOICE",
            values=('foo', 'bar', 'go' 'away', 'plz',)
        )

class IGrandfather(Schema):
    pass

class IGrandmother(Schema):
    pass

class IFather(IGrandfather, IGrandmother):
    pass

class IUncle(IGrandfather, IGrandmother):
    pass

class IAunt(IGrandfather, IGrandmother):
    pass

class IBrother(IFather):
    pass

class ISister(IFather):
    pass
