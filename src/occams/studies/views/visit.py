from pyramid.view import view_config
import wtforms.fields.html5
import wtforms.widgets.html5

from occams.studies import _


@view_config(
    route_name='patient_visits',
    permission='visit_view',
    renderer='../templates/event/list.pt')
def list_(request):
    return {}


@view_config(
    route_name='patient_visits',
    permission='visit_add',
    request_method='POST',
    xhr=True,
    renderer='json')
def add(request):
    form = EventAddForm(request.POST)
    if request.method == 'POST' and form.validate():
        pass
    return {'form': form}


class PatientSubForm(wtforms.Form):

    is_new = wtforms.BooleanField(
        label=_(u'Create'),
        widget=wtforms.widgets.CheckboxInput())

    pid = wtforms.StringField()


class ScheduleSubForm(wtforms.Form):

    study = wtforms.StringField(
        label=_(u'Study'))

    schedule = wtforms.StringField(
        label=_(u'Schedule'))


class EventAddForm(wtforms.Form):

    patient = wtforms.FormField(
        PatientSubForm,
        label=_(u'Patient'),
        description=_(
            u'Please specify the patient to add the event for. '
            u'You may also create a new patient'),
        validators=[wtforms.validators.required()])

    event_date = wtforms.fields.html5.DateField(
        label=_(u'Event Date'),
        description=_(u'The date the event took place.'),
        validators=[wtforms.validators.required()])

    schedules = wtforms.FieldList(
        wtforms.FormField(ScheduleSubForm),
        label=_(u'Schedules'),
        description=_(
            u'(Optional) The study schedule that applies to this event'))
