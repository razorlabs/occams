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
from occams.form.interfaces import IEditableForm
from occams.datastore import model
from z3c.form import button
from occams.datastore.schema import copy
from z3c.form.interfaces import DISPLAY_MODE
from zope.security import checkPermission

from occams.form.form import UserAwareMixin
from occams.form.serialize import camelize

additionalControls = [('view', _(u'View')), ('edit', _(u'Edit')), ]
links = dict(view='@@view', edit='@@edit',)

class ListingEditSubForm(crud.EditSubForm):

    def _select_field(self):
        select_field = super(ListingEditSubForm, self)._select_field()
        if self.content.state == 'retracted' or not \
            ( checkPermission("occams.form.DraftForm", self.context) or \
                checkPermission("occams.form.RemoveForm", self.context) ):
            select_field.mode = DISPLAY_MODE
        return select_field

    def updateWidgets(self):
        super(ListingEditSubForm, self).updateWidgets()
        stateWidget = 'view_state' in self.widgets and self.widgets['view_state'] or None
        isCurrentWidget = 'view_current' in self.widgets and self.widgets['view_current'] or None

        if stateWidget:
            stateWidget.addClass(str(stateWidget.value))
            if stateWidget.value == 'retracted':
                for widget in self.widgets.values():
                    widget.addClass('retracted')             
        if isCurrentWidget and self.content.is_current:
            isCurrentWidget.addClass('is_current')
            isCurrentWidget.value='current'

        for name, title in additionalControls:
            if name != 'edit' or (self.content.is_editable and checkPermission('occams.form.ModifyForm', self.context)):
                self.widgets['view_' + name].value = title
            else:
                self.widgets['view_' + name].value = ''


class ListingEditForm(crud.EditForm):
    """
    Custom form edit form.
    """

    label = None
    editsubform_factory = ListingEditSubForm

    def can_draft(self):
        return  checkPermission("occams.form.ModifyForm", self.context) 

    @button.buttonAndHandler(_('Draft New Version'), name='draft', condition= lambda self: self.can_draft())
    def handleDraft(self, action):
        selected = self.selected_items()
        session_name = self.context.context.session
        if selected:
            Session = named_scoped_session(session_name)
            for obj_id, obj in selected:
                old_schema = Session.query(model.Schema).filter(model.Schema.id == obj_id).one()
                new_schema = copy(old_schema)
                Session.add(new_schema)
            Session.flush()
        return self.request.response.redirect(self.action)

    def can_retract(self):
        return  checkPermission("occams.form.RemoveForm", self.context) 

    @button.buttonAndHandler(_('Retract'), name='retract', condition= lambda self: self.can_retract())
    def handleRetract(self, action):
        selected = self.selected_items()
        session_name = self.context.context.session
        if selected:
            Session = named_scoped_session(session_name)
            for obj_id, obj in selected:
                schema = Session.query(model.Schema).filter(model.Schema.id == obj_id).one()
                if not schema.publish_date:
                    Session.delete(schema)
                else:
                    schema.state='retracted'
            Session.flush()
        return self.request.response.redirect(self.action)

class AddForm(crud.AddForm):
    """
    """
    label = _(u"Add a new form")

class SummaryListingForm(crud.CrudForm, UserAwareMixin):
    """
    Lists the forms in the repository.
    No add form is needed as that will be a separate view.
    See ``configure.zcml`` for directive configuration.
    """

    @property
    def addform_factory(self):
        if checkPermission("occams.form.CreateForm", self.context):
            return AddForm
        return crud.NullForm
    editform_factory = ListingEditForm

    _items = None

    add_schema = z3c.form.field.Fields(IEditableForm).omit('name', 'publish_date')

    @property
    def label(self):
        return self.context.title

    @property
    def description(self):
        return self.context.description

    def add(self, data):
        Session = named_scoped_session(self.context.session)

        newSchema = model.Schema(
                name = camelize(data['title']),
                title = unicode(data['title']),
                description = unicode(data['description']),
                state = 'draft'
                )
        Session.add(newSchema)
        Session.flush()
        return newSchema

    def update(self):
        # Don't use changes count, apparently it's too confusing for users
        field = zope.schema.TextLine(__name__='current', title=u'')
        view_schema = z3c.form.field.Fields(field)
        view_schema += z3c.form.field.Fields(IFormSummary).omit('id', 'name', 'is_editable', 'is_current')

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
        if field == 'view' and item.publish_date:
        # if field in links:
            return os.path.join(self.context.absolute_url(), item.name+'-'+item.publish_date.isoformat(), links[field])
        elif field == 'view':
            return os.path.join(self.context.absolute_url(), str(item.id), links[field])
        elif field == 'edit' and item.is_editable and checkPermission('occams.form.ModifyForm', self.context):
            return os.path.join(self.context.absolute_url(), str(item.id), links[field])
      


Listing = layout.wrap_form(SummaryListingForm)
