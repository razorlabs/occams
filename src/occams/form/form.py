#""" 
#Form translators. 
#beast.datastore <-> z3c.form
#"""
#
#
#from copy import copy
#import re
#
#from zope.component import getMultiAdapter
#from zope.interface import alsoProvides
#from zope.interface.interface import InterfaceClass
#import zope.schema
#
#from five import grok
#from plone.directives import form
#from plone.directives.form.schema import TEMP_KEY
#from plone.directives.form.schema import FIELDSETS_KEY
#from plone.directives.form.schema import WIDGETS_KEY
#from plone.supermodel.model import Fieldset
#
#
##from avrc.aeh.interfaces import ICaseReportFormFormat
#from avrc.data.store import directives as datastore
#from avrc.data.store.interfaces import ISchemaFormat
#from avrc.data.store.storage import ObjectFactory
#
#
#def _getAutoFormValue(iface, key):
#    values = iface.queryTaggedValue(key)
#    if not values:
#        tagged_values = iface.queryTaggedValue(TEMP_KEY)
#        if tagged_values and key in tagged_values:
#            values = tagged_values.get(key)
#    return values
#
#@grok.adapter()
#@grok.implementer()
#def SchemaToForm(schema):
#    pass
#
#@grok.adapter(ISchemaFormat)
#@grok.implementer(ICaseReportFormFormat)
#def SchemaFormatConverter(schema):
#    """ Converts DataStore schema to an AEH Format. This is because Plone
#        cannot elegantly display sub forms correctly so when the UI is rendered
#        the form will simply be flattened.
#    """
#    if datastore.Schema not in schema.getBases():
#        bases = [ICaseReportFormFormat(base) for base in schema.getBases()]
#    else:
#        bases = [form.Schema]
#
#    directives = {FIELDSETS_KEY: [], WIDGETS_KEY: dict()}
#    widgets = dict()
#    fields = dict()
#    order = 0
#
#    for name, attribute in zope.schema.getFieldsInOrder(schema):
#        queue = list()
#        if isinstance(attribute, zope.schema.Object):
#            fieldset = Fieldset(
#                __name__=attribute.__name__,
#                label=attribute.title,
#                description=attribute.description,
#                fields=zope.schema.getFieldNamesInOrder(attribute.schema)
#                )
#            directives[FIELDSETS_KEY].append(fieldset)
#            for subname, subfield in zope.schema.getFieldsInOrder(attribute.schema):
#                queue.append(copy(subfield))
#        else:
#            queue.append(copy(attribute))
#
#        for field in queue:
#            order += 1
#            widget = datastore.widget.bind().get(field)
#            if widget is not None:
#                directives[WIDGETS_KEY][field.__name__] = widget
#                widgets[field.__name__] = widget
#            field.order = order
#            fields[field.__name__] = field
#
#    crf = InterfaceClass(
#        __doc__=schema.__doc__,
#        name=schema.__name__,
#        bases=bases,
#        attrs=fields,
#        )
#
#    alsoProvides(crf, ICaseReportFormFormat)
#
#    for key, item in directives.items():
#        crf.setTaggedValue(key, item)
#
#    datastore.title.set(crf, datastore.title.bind().get(schema))
#    datastore.description.set(crf, datastore.title.bind().get(schema))
#    datastore.version.set(crf, datastore.version.bind().get(schema))
#
#    return crf
#
#
#@grok.adapter(ICaseReportFormFormat)
#@grok.implementer(ISchemaFormat)
#def CaseReportFormatConverter(crf):
#    """ Converts AEH style forms to DataStore format schemata. 
#        This is intended for legacy forms designed before versioning.
#        Useful for import.
#    """
#    if form.Schema not in crf.getBases():
#        bases = [ISchemaFormat(base) for base in crf.getBases()]
#    else:
#        bases = [datastore.Schema]
#
#    fieldsets = _getAutoFormValue(crf, FIELDSETS_KEY)
#    widgets = _getAutoFormValue(crf, WIDGETS_KEY)
#    processed = set()
#    fields = dict()
#
#    if fieldsets:
#        for order, fieldset in enumerate(fieldsets, start=1):
#            title = u'%s %s' % (crf.__name__, fieldset.label)
#            name = re.sub(r'\W+', '_', u''.join(title.split()))
#            subfields = dict()
#            subbases = [datastore.Schema]
#
#            for field_name in fieldset.fields:
#                field = copy(crf[field_name])
#                if isinstance(getattr(field, 'value_type', field), zope.schema.Choice):
#                    datastore.type.set(field, u'string')
#                subfields[field.__name__] = field
#                processed.add(field_name)
#                if widgets and field_name in widgets:
#                    datastore.widget.set(subfields[field.__name__], widgets[field_name])
#
#            subschema = InterfaceClass(name=name, bases=subbases, attrs=subfields)
#            datastore.title.set(subschema, title)
#            datastore.description.set(subschema, fieldset.description)
#
#            field = zope.schema.Object(
#                __name__=fieldset.__name__,
#                title=fieldset.label,
#                description=fieldset.description,
#                schema=subschema,
#                required=False,
#                )
#
#            datastore.inline.set(field, True)
#
#            field.order = order
#            fields[fieldset.__name__] = field
#
#    for name, field in zope.schema.getFieldsInOrder(crf):
#        field = copy(field)
#        if name not in processed:
#            if isinstance(getattr(field, 'value_type', field), zope.schema.Choice):
#                datastore.type.set(field, u'string')
#            fields[field.__name__] = field
#            processed.add(name)
#            if widgets and name in widgets:
#                datastore.widget.set(fields[name], widgets[name])
#
#    schema = InterfaceClass(
#        __doc__=crf.__doc__,
#        name=crf.__name__,
#        bases=bases,
#        attrs=fields,
#        )
#
#    alsoProvides(schema, ISchemaFormat)
#
#    datastore.title.set(schema, datastore.title.bind().get(crf))
#    datastore.description.set(schema, datastore.description.bind().get(crf))
#
#    return schema
#
#
#@grok.adapter(datastore.Schema, ICaseReportFormFormat)
#@grok.implementer(form.Schema)
#def SchemaDataFormatConverter(item, crf):
#    """ Converts DataStore data to CRF format.
#    """
#    values = dict()
#    names = dict()
#
#    names[item.__schema__.__name__] = (item.__id__, item.__name__, item.__title__, item.__version__)
#
#    for name, field in zope.schema.getFieldsInOrder(item.__schema__):
#        if isinstance(field, zope.schema.Object):
#            subitem = getattr(item, name, None)
#            if subitem is not None:
#                metadata = (subitem.__id__, subitem.__name__, subitem.__title__, subitem.__version__)
#                for subname, subfield in zope.schema.getFieldsInOrder(field.schema):
#                    value = getattr(subitem, subname, None)
#                    values[subname] = value
#            else:
#                metadata = (None, None, None, None)
#                values.update(dict.fromkeys(zope.schema.getFieldNames(field.schema)))
#            names[field.schema.__name__] = metadata
#
#        else:
#            value = getattr(item, name, None)
#            values[name] = value
#
#    result = ObjectFactory(crf, **values)
#
#    result.__dict__.update(dict(
#        __schema__=crf,
#        __state__=item.__state__,
#        __name__=item.__name__,
#        __title__=item.__title__,
#        __metadata__=names,
#        ))
#
#    return result
#
#
#@grok.adapter(form.Schema, ISchemaFormat)
#@grok.implementer(datastore.Schema)
#def CaseReportDataFormatConverter(item, schema):
#    """ Converts CRF data to DataStore objects.
#    """
#    values = dict()
#
#    for name, field in zope.schema.getFieldsInOrder(schema):
#        if isinstance(field, zope.schema.Object):
#            value = getMultiAdapter((item, field.schema), datastore.Schema)
#        else:
#            value = getattr(item, name, None)
#        values[name] = value
#
#    result = ObjectFactory(schema, **values)
#
#    if hasattr(item, '__metadata__'):
#        (id, name, title, version) = item.__metadata__[schema.__name__]
#    else:
#        id = name = title = version = None
#
#    result.__dict__.update(dict(
#        __id__=id,
#        __schema__=schema,
#        __state__=item.__state__,
#        __name__=name,
#        __title__=title,
#        __version__=version,
#        ))
#
#    return result
