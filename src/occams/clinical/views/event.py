import colander
import deform
from pyramid_deform import CSRFSchema
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from sqlalchemy import func, orm, sql
import transaction

from occams.datastore import model as datastore
import occams.form.widgets

from .. import _, log, models, Session, widgets


class EventAddSchema(CSRFSchema):

    @colander.instantiate(
        title=_(u'Patient'),
        description=_(
            u'Please specify the patient to add the event for. '
            u'You may also create a new patient'),
        widget=occams.form.widgets.GroupInputWidget(before='is_new'),
        required=True)
    class patient(colander.MappingSchema):

        is_new = colander.SchemaNode(
            colander.Bool(),
            widget=deform.widget.CheckboxWidget(),
            label=_(u'New'))

        pid = colander.SchemaNode(
            colander.String(),
            missing=None)

    event_date = colander.SchemaNode(
        colander.Date(),
        title=_(u'Event Date'),
        description=_(u'The date the event took place.'),
        required=True)

    @colander.instantiate(
        description=_(
            u'(Optional) The study schedule that applies to this event'),
        missing=None)
    class schedules(colander.SequenceSchema):

        @colander.instantiate()
        class schedule(colander.MappingSchema):

            study = colander.SchemaNode(
                colander.String())

            schedule = colander.SchemaNode(
                colander.String())


@view_config(
    route_name='event_add',
    permission='event_add',
    renderer='occams.clinical:templates/event/add.pt')
def add(request):
    schema = EventAddSchema().bind(request=request)
    form = deform.Form(
        schema,
        buttons=[
            deform.Button('submit', _(u'Submit'),
                css_class='btn btn-primary pull-right'),
            deform.Button('cancel', _(u'Cancel'),
                type='button', css_class='btn btn-link pull-right')])
    return {'form': form.render()}


@view_config(
    route_name='event_list',
    permission='event_view',
    renderer='occams.clinical:templates/event/list.pt')
def list_(request):
    return {}

