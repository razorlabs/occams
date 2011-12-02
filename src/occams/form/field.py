
from zope.schema import getFieldNames

from five import grok

from occams.form.interfaces import IAttributeContext
from occams.form.interfaces import IEditableField


class EditableStringField(grok.Adapter):
    grok.context(IAttributeContext)
    grok.provides(IEditableField)
#
#    def __call__(self):
#        result = dict()
#        for name in getFieldNames(IEditableField):
#            return
#        result = dict()
#        return dict(
#            name=,
#            title=,
#            description=,
#            is_required=,
#            is_collection=,
#            )
#        self.name = self.context.item.name
#        self.title = self.context.item.title
#        self.description = self.context.item.description
#        self.is_required = self.context.item.is_required
#        self.is_collection = self.context.item.is_collection
