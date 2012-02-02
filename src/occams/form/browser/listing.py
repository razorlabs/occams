import os.path

from plone.z3cform import layout
from plone.z3cform.crud import crud
from zope.component import getUtility
import zope.schema
import z3c.form.button
import z3c.form.field

from avrc.data.store.interfaces import IDataStore
from avrc.data.store import directives as datastore
from occams.form import MessageFactory as _
from occams.form.interfaces import IFormSummary
from occams.form.interfaces import IFormSummaryGenerator


class ListingEditSubForm(crud.EditSubForm):

    def updateWidgets(self):
        super(ListingEditSubForm, self).updateWidgets()
        self.widgets['view_edit'].value = _(u'Edit')


class ListingEditForm(crud.EditForm):
    """
    Custom form edit form.
    """

    label = None

    editsubform_factory = ListingEditSubForm

    # No buttons for this release
    buttons = z3c.form.button.Buttons()


class SummaryListingForm(crud.CrudForm):
    """
    Lists the forms in the repository.
    No add form is needed as that will be a separate view.
    See ``configure.zcml`` for directive configuration.
    """

    addform_factory = crud.NullForm
    editform_factory = ListingEditForm

    # don't use changes count, apparently it's too confusing for users
    view_schema = z3c.form.field.Fields(IFormSummary).omit('name', 'changeCount')
    view_schema += z3c.form.field.Fields(
        zope.schema.TextLine(__name__='edit', title=u'')
        )

    _items = None

    def get_items(self):
        """
        Return a listing of all the forms.
        """
        # Plone seems to call this method more than once, so make sure
        # we return an already generated listing.
        if self._items is None:
            datastore = IDataStore(self.context)
            generator = getUtility(IFormSummaryGenerator)
            listing = generator.getItems(datastore.session)
            self._items = [(summary.name, summary) for summary in listing]
        return self._items

    def link(self, item, field):
        """
        Renders a link to the form view
        """
        if field == 'title':
            # Redirect to the editor for now, until we can get some stats
            return os.path.join(self.context.absolute_url(), item.name)

        if field == 'edit':
            item.edit = 'Edit'
            return os.path.join(self.context.absolute_url(), item.name, '@@edit')


class Listing(layout.FormWrapper):
    """
    Form wrapper so it can be rendered with a Plone layout and dynamic title.
    """

    form = SummaryListingForm

    @property
    def label(self):
        return self.context.title

    @property
    def description(self):
        return self.context.description

