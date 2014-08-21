from pyramid.view import view_config
import wtforms.fields.html5
import wtforms.widgets.html5

from occams.studies import _


@view_config(
    route_name='visits',
    permission='visit_view',
    renderer='../templates/event/list.pt')
def list_(request):
    return {}


@view_config(
    route_name='visits',
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


def get_visits_data(request, patient):
    return [{
        '__url__': request.route_path(
            'visit',
            patient=patient.pid,
            visit=v.visit_date.isoformat()),
        'id': v.id,
        'cycles': [{
            'id': c.id,
            'study': {
                'id': c.study.id,
                'name': c.study.name,
                'title': c.study.title,
                'code': c.study.code
                },
            'name': c.name,
            'title': c.title,
            'week': c.week
            } for c in v.cycles],
        'visit_date': v.visit_date.isoformat(),
        'forms_complete': len(
            [e for e in v.entities if e.state.name == 'complete']),
        'forms_total': len(v.entities)
        } for v in patient.visits]


def validate_visit_cycle(request, patient, visit=None):
    def validator(value):
        lz = get_localizer(request)
        (exists,) = (
            Session.query(
                Session.query(models.Cycle)
                .filter_by(id=value)
                .exists()
            ).one())
        if not exists:
            raise Invalid(lz.translate(_(
                u'Specified a cycle that does not exist')))
        # TODO need a mechanism to check if the cycle can be repeated,
        # for not just block all repetions, vaya con Dios...
        taken_query = (
            Session.query(model.Visit)
            .filter(model.Visit.patient == patient)
            .filter(models.Visit.cycles.any(id=value)))
        if visit:
            taken_query = taken_query.filter(model.Visit.id != visit.id)
        taken = taken_query.first()
        if taken:
            raise Invalid(lz.translate(
                _(u'Cycle is already being used by visit on ${visit_date}'),
                mapping={'visit_date': taken.visit_date}))
        return value
    return validator


def VisitSchema(request, patient, visit=None):
    lz = get_localizer(request)
    return Schema({
        Required('cycle_ids'): All(
            [All(Coerce(int), validate_visit_cycle(request, patient, visit))],
            Length(
                min=1,
                msg=lz.translate(_(u'Must select at least one cycle')))),
        Required('visit_date'): Date(),
        Optional('add_forms'): bool
        })
