import os.path

from zope.component import getUtility
from zope.interface import implements

from plone.z3cform import layout
from plone.z3cform.crud import crud
import z3c.form.button
import z3c.form.field

from avrc.data.store.interfaces import IDataStore
from avrc.data.store import directives as datastore

from occams.form.interfaces import IOccamsBrowserView
from occams.form.interfaces import IFormSummary
from occams.form.interfaces import IFormSummaryGenerator


class ListingEditForm(crud.EditForm):
    """
    Custom form edit form.
    """
    label = None

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


class Listing(layout.FormWrapper):
    """
    Form wrapper so it can be rendered with a Plone layout and dynamic title.
    """
    implements(IOccamsBrowserView)

    form = SummaryListingForm

    @property
    def label(self):
        return self.context.title

    @property
    def description(self):
        return self.context.description

