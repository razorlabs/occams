"""
Editor for possible workflow states
"""

from plone.z3cform.crud import crud
from plone.z3cform import layout
import zope.interface
import z3c.form.validator
from z3c.saconfig.interfaces import IScopedSession

from avrc.data.store import model
from occams.form import MessageFactory as _
from occams.form.interfaces import IEditableState


class WorkflowStateListingForm(crud.CrudForm):

    update_schema = IEditableState

    label = _(u'Workflow States')

    description = _(
        u'This page is intended for modifying possible workflow states of '
        u'form items. Please be aware that some parts of the product depend '
        u'on the names of the states, so use caution when modifying state '
        u'names'
        )

    def get_items(self):
        items = []
        session = IScopedSession(self.context)
        query = (
            session.query(model.State)
            .filter(model.State.is_active == True)
            .order_by(model.State.name)
            )
        for state in query.all():
            items.append((state.id, dict(
                id=state.id,
                name=state.name,
                title=state.title,
                description=state.description,
                )))
        return items

    def add(self, data):
        session = IScopedSession(self.context)
        state = model.State(**data)
        session.add(state)
        session.flush()
        return data

    def before_update(self, item, data):
        session = IScopedSession(self.context)
        state = session.query(model.State).filter_by(name=item['name']).first()
        state.name = data['name']
        state.title = data['title']
        state.description = data['description']
        session.flush()

    def remove(self, (id, item)):
        session = IScopedSession(self.context)
        state = session.query(model.State).get(id)
        if state is not None:
            state.is_active = False
            session.flush()


WorkflowStateListing = layout.wrap_form(WorkflowStateListingForm)


class StateNameValidator(z3c.form.validator.SimpleFieldValidator):

    def validate(self, value):
        super(StateNameValidator, self).validate(value)

        # Edit forms use an extra subform, so check if it's either edit or add
        if isinstance(self.view, crud.AddForm):
            repository = self.view.context.context
        else:
            repository = self.view.context.context.context

        session = IScopedSession(repository)
        query = session.query(model.State).filter_by(name=unicode(value))

        # If editing, omit the current item in the check
        if isinstance(self.view, crud.EditSubForm):
            query = query.filter(model.State.id != self.view.content_id)

        # Make sure we're not adding a state with name conflicts
        if query.count():
            raise zope.interface.Invalid('"%s" already exists' % value)


z3c.form.validator.WidgetValidatorDiscriminators(
    validator=StateNameValidator,
    field=IEditableState['name'],
    )
