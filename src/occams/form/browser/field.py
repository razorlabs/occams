import z3c.form.form
import z3c.form.button
import z3c.form.field

from zope.interface import Interface
from zope.interface import implements
import zope.schema

from occams.form import MessageFactory as _
from occams.form.interfaces import IOccamsBrowserView


class IField(Interface):

    name = zope.schema.ASCIILine(
        title=_(u'Variable Name'),
        readonly=True,
        )

    title = zope.schema.TextLine(
        title=_(u'Label')
        )

    description = zope.schema.Text(
        title=_(u'Description'),
        required=False,
        )

    is_required = zope.schema.Bool(
        title=_(u'Required?'),
        default=False,
        )

    is_collection = zope.schema.Bool(
        title=_(u'Multiple?'),
        default=False,
        )


class Edit(z3c.form.form.Form):
    implements(IOccamsBrowserView)

    ignoreContext = True
    ignoreRequest = True

    fields = z3c.form.field.Fields(IField)

    @property
    def label(self):
        return 'Edit: %s' % self.context.item.name

    def update(self):
        self.request.set('disable_border', True)
        self._updateHelper()
        super(Edit, self).update()

    def _updateHelper(self):
        return

    @z3c.form.button.buttonAndHandler(_(u'Save'), name='save')
    def save(self):
        return

    @z3c.form.button.buttonAndHandler(_(u'Cancel'), name='cancel')
    def cancel(self):
        return
