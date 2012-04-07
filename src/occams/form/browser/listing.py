import os.path

from plone.z3cform import layout
from plone.z3cform.crud import crud
from zope.component import getUtility
import zope.schema
import z3c.form.button
import z3c.form.field
from z3c.saconfig import named_scoped_session
from occams.form import MessageFactory as _
from occams.form.interfaces import IFormSummary
from occams.form.interfaces import IFormSummaryGenerator
from occams.datastore import model
from z3c.form import button
from occams.datastore.schema import copy

from occams.form.form import UserAwareMixin

additionalControls = [('view', _(u'View')), ('edit', _(u'Edit')), ]
links = dict(view='@@view', edit='@@edit',)

class ListingEditSubForm(crud.EditSubForm):

    # def _select_field(self):
    #     """
    #     Cancels the rendering of the check box as we can't delete forms
    #     as of this release.
    #     """
    #     return z3c.form.field.Fields()

    def updateWidgets(self):
        super(ListingEditSubForm, self).updateWidgets()
        for name, title in additionalControls:
            if name != 'edit' or self.content.draft_id:
                self.widgets['view_' + name].value = title
            else:
                self.widgets['view_' + name].value = ''


class ListingEditForm(crud.EditForm):
    """
    Custom form edit form.
    """

    label = None
    editsubform_factory = ListingEditSubForm

    @button.buttonAndHandler(_('Draft New Version'), name='draft')
    def handleDraft(self, action):
        selected = self.selected_items()
        session_name = self.context.context.session
        if selected:
            Session = named_scoped_session(session_name)
            for obj_id, obj in selected:
                if obj.draft_id:
                    continue
                old_schema = Session.query(model.Schema).filter(model.Schema.id == obj_id).one()
                new_schema = copy(old_schema)
                Session.add(new_schema)
            Session.flush()
        return self.request.response.redirect(self.action)


    @button.buttonAndHandler(_('Delete'), name='delete')
    def handleDelete(self, action):
        raise Exception('NO!')
        
class SummaryListingForm(crud.CrudForm, UserAwareMixin):
    """
    Lists the forms in the repository.
    No add form is needed as that will be a separate view.
    See ``configure.zcml`` for directive configuration.
    """

    addform_factory = crud.NullForm
    editform_factory = ListingEditForm

    _items = None

    @property
    def label(self):
        return self.context.title

    @property
    def description(self):
        return self.context.description

    def update(self):
        # Don't use changes count, apparently it's too confusing for users
        view_schema = z3c.form.field.Fields(IFormSummary).omit('id', 'name', 'draft_id')

        # Add controls
        for name, title in additionalControls:
            field = zope.schema.TextLine(__name__=name, title=u'')

            view_schema += z3c.form.field.Fields(field)

        self.view_schema = view_schema
        super(SummaryListingForm, self).update()

    def get_items(self):
        """
        Return a listing of all the forms.
        """
        # Plone seems to call this method more than once, so make sure
        # we return an already generated listing.
        if self._items is None:
            generator = getUtility(IFormSummaryGenerator)
            listing = generator.getItems(named_scoped_session(self.context.session))
            self._items = [(summary.id, summary) for summary in listing]
        return self._items

    def link(self, item, field):
        """
        Renders a link to the form view
        """
        if field == 'view':
        # if field in links:
            return os.path.join(self.context.absolute_url(), item.name+'-'+item.publish_date.isoformat(), links[field])
        elif field == 'edit' and item.draft_id is not None:
            return os.path.join(self.context.absolute_url(), str(item.draft_id), links[field])
      


Listing = layout.wrap_form(SummaryListingForm)
