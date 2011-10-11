"""
Tools for rendering a form (since subforms aren't well supported)
"""

from copy import copy

from zope.interface.interface import InterfaceClass
import zope.schema
from z3c.form import field

from plone.directives import form
from plone.directives.form.schema import FIELDSETS_KEY
from plone.directives.form.schema import WIDGETS_KEY
from plone.supermodel.model import Fieldset

from avrc.data.store import directives as datastore


def convertSchemaToForm(schema):
    """
    Converts a DataStore form to a Dexterity Form
    """
    if datastore.Schema not in schema.getBases():
        bases = [convertSchemaToForm(base) for base in schema.getBases()]
    else:
        bases = [form.Schema]

    directives = {FIELDSETS_KEY: [], WIDGETS_KEY: dict()}
    widgets = dict()
    fields = dict()
    order = 0

    for name, attribute in zope.schema.getFieldsInOrder(schema):
        queue = list()
        if isinstance(attribute, zope.schema.Object):
            fieldset = Fieldset(
                __name__=attribute.__name__,
                label=attribute.title,
                description=attribute.description,
                fields=zope.schema.getFieldNamesInOrder(attribute.schema)
                )
            directives[FIELDSETS_KEY].append(fieldset)
            for subname, subfield in zope.schema.getFieldsInOrder(attribute.schema):
                queue.append(copy(subfield))
        else:
            queue.append(copy(attribute))

        for field in queue:
            order += 1
            widget = datastore.widget.bind().get(field)
            if widget is not None:
                directives[WIDGETS_KEY][field.__name__] = widget
                widgets[field.__name__] = widget
            field.order = order
            fields[field.__name__] = field

    ploneForm = InterfaceClass(
        __doc__=schema.__doc__,
        name=schema.__name__,
        bases=bases,
        attrs=fields,
        )

    for key, item in directives.items():
        ploneForm.setTaggedValue(key, item)

    datastore.title.set(ploneForm, datastore.title.bind().get(schema))
    datastore.description.set(ploneForm, datastore.title.bind().get(schema))
    datastore.version.set(ploneForm, datastore.version.bind().get(schema))

    return ploneForm
