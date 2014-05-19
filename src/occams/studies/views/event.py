from pyramid.view import view_config
from wtforms import (
    Form,
    FormField,
    FieldList,
    StringField,
    BooleanField,
    validators,
    widgets
)
from wtforms.fields.html5 import DateField

from occams.studies import _
from occams.studies.utils.form import CSRFForm


class PatientSubForm(Form):

    is_new = BooleanField(
        label=_(u'Create'),
        widget=widgets.CheckboxInput())

    pid = StringField()


class ScheduleSubForm(Form):

    study = StringField(
        label=_(u'Study'))

    schedule = StringField(
        label=_(u'Schedule'))


class EventAddForm(CSRFForm):

    patient = FormField(
        PatientSubForm,
        label=_(u'Patient'),
        description=_(
            u'Please specify the patient to add the event for. '
            u'You may also create a new patient'),
        #widget=occams.form.widgets.GroupInputWidget(before='is_new'),
        validators=[validators.required()])

    event_date = DateField(
        label=_(u'Event Date'),
        description=_(u'The date the event took place.'),
        validators=[validators.required()])

    schedules = FieldList(
        FormField(ScheduleSubForm),
        label=_(u'Schedules'),
        description=_(
            u'(Optional) The study schedule that applies to this event'))


@view_config(
    route_name='event_add',
    permission='event_add',
    xhr=True,
    renderer='json')
def add(request):
    form = EventAddForm(request.POST)
    if request.method == 'POST' and form.validate():
        pass
    return {'form': form}


@view_config(
    route_name='event_list',
    permission='event_view',
    renderer='occams.studies:templates/event/list.pt')
def list_(request):
    return {}
