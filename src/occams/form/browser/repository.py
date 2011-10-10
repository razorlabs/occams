import os

from z3c.form import field

from plone.z3cform import layout
from plone.z3cform.crud import crud

from avrc.data.store.interfaces import IDataStore
from avrc.data.store import model

from occams.form.interfaces import IFormSummary


class FormEditForm(crud.EditForm):
    """
    Custom form edit form.
    """
    label = None
    buttons = crud.EditForm.buttons.copy()
    handlers = crud.EditForm.handlers.copy()


class FormListing(crud.CrudForm):
    """
    Lists the forms in the repository.
    No add form is needed as that will be a separate view.
    See ``configure.zcml`` for directive configuration.
    """

    addform_factory = crud.NullForm
    editform_factory = FormEditForm
    view_schema = field.Fields(IFormSummary)

    def get_items(self):
        """
        Return a listing of all the forms.
        """
        datastore = IDataStore(self.context)
        session = datastore.session
        query = (
            session.query(model.Schema)
            .filter(model.Schema.asOf(None))
            .order_by(model.Schema.name.asc())
            )
        items = [(str(schema.name), IFormSummary(schema)) for schema in query.all()]
        return items

    def link(self, item, field):
        """
        Renders a link to the form view
        """
        if field == 'title':
            return os.path.join(self.context.absolute_url(), 'form', item.context.name)


class FormListingPage(layout.FormWrapper):
    """
    Form wrapper so it can be rendered with a Plone layout and dynamic title.
    """

    form = FormListing

    @property
    def label(self):
        return self.context.Title()
