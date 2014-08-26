from pyramid.i18n import get_localizer
from pyramid.view import view_config
import six
import sqlalchemy as sa
from sqlalchemy import orm
from voluptuous import *  # NOQA

from occams.studies import _, models, Session
from occams.studies.validators import Date


@view_config(
    route_name='visit',
    permission='view',
    renderer='../templates/visit/view.pt')
def view(context, request):

    entities_query = (
        Session.query(models.Entity)
        .options(orm.joinedload('schema'), orm.joinedload('state'))
        .join(models.Context)
        .filter_by(external='visit', key=context.id))

    return {
        'visit_data': {
            '__url__': request.current_route_path(_route_name='visit'),
            'id': context.id,
            'cycles': [{
                'id': cycle.id,
                'study': {
                    'id': cycle.study.id,
                    'name': cycle.study.name,
                    'title': cycle.study.title,
                    'code': cycle.study.code
                    },
                'name': cycle.name,
                'title': cycle.title,
                'week': cycle.week
                } for cycle in context.cycles],
            'patient': {
                '__url__': request.current_route_path(_route_name='patient'),
                'site': {
                    'title': context.patient.site.title,
                    },
                'pid': context.patient.pid
                },
            'visit_date': context.visit_date.isoformat(),
            'entities': [{
                '__url__': request.current_route_path(_route_name='visit_form',
                                                      form=entity.id),
                'id': entity.id,
                'schema': {
                    'name': entity.schema.name,
                    'title': entity.schema.title,
                    },
                'collect_date': entity.collect_date.isoformat(),
                'not_done': entity.not_done,
                'state': {
                    'id': entity.state.id,
                    'title': entity.state.title,
                    }
                } for entity in entities_query]
            }
        }


@view_config(
    route_name='visit',
    permission='add',
    request_method='POST',
    xhr=True,
    renderer='json')
def add(context, request):
    form = EventAddForm(request.POST)
    if request.method == 'POST' and form.validate():
        pass
    return view(context, request)


def get_visit_data(request, visit):
    return {
        '__url__': request.route_path(
            'visit',
            patient=patient.pid,
            visit=visit.visit_date.isoformat()),
        'id': visit.id,
        'cycles': [{
            'id': cycle.id,
            'study': {
                'id': cycle.study.id,
                'name': cycle.study.name,
                'title': cycle.study.title,
                'code': cycle.study.code
                },
            'name': cycle.name,
            'title': cycle.title,
            'week': cycle.week
            } for cycle in visit.cycles],
        'visit_date': visit.visit_date.isoformat(),
        'forms_complete': progress.get('complete', 0),
        'forms_incomplete': sum(v for k, v in six.iteritems(progress)
                                if k not in ('complete', 'pending-entry')),
        'forms_not_started': progress.get('pending-entry', 0),
        'forms_total': sum(v for v in six.itervalues(progress))
        }


def get_visits_data(request, patient):

    def visit_progress(visit):
        """
        Returns a dictionary of the states of the entities in the visit
        """
        entities_query = (
            Session.query(
                models.State.name,
                sa.func.count())
            .select_from(models.Entity)
            .join(models.Entity.state)
            .join(models.Context)
            .filter(models.Context.external == 'visit')
            .filter(models.Context.key == visit.id)
            .group_by(models.State.name))
        return dict(entities_query.all())

    def visit_data(visit):
        """
        Generats the actual visit data
        """
        progress = visit_progress(visit)
        return {
            '__url__': request.route_path(
                'visit',
                patient=patient.pid,
                visit=visit.visit_date.isoformat()),
            'id': visit.id,
            'cycles': [{
                'id': cycle.id,
                'study': {
                    'id': cycle.study.id,
                    'name': cycle.study.name,
                    'title': cycle.study.title,
                    'code': cycle.study.code
                    },
                'name': cycle.name,
                'title': cycle.title,
                'week': cycle.week
                } for cycle in visit.cycles],
            'visit_date': visit.visit_date.isoformat(),
            'forms_complete': progress.get('complete', 0),
            'forms_incomplete': sum(v for k, v in six.iteritems(progress)
                                    if k not in ('complete', 'pending-entry')),
            'forms_not_started': progress.get('pending-entry', 0),
            'forms_total': sum(v for v in six.itervalues(progress))
            }

    visits_query = (
        Session.query(models.Visit)
        .options(
            orm.joinedload(models.Visit.cycles).joinedload(models.Cycle.study))
        .filter_by(patient=patient)
        .order_by(models.Visit.visit_date.desc()))

    return [visit_data(v) for v in visits_query]


def VisitSchema(request, patient, visit=None):
    lz = get_localizer(request)
    return Schema({
        Required('cycle_ids'): All(
            [All(Coerce(int), valid_cycle(request))],
            Length(
                min=1,
                msg=lz.translate(_(u'Must select at least one cycle')))),
        Required('visit_date'): Date(),
        Optional('add_forms'): Boolean(),
        Extra: object
        }, unqique_visit_cycle)


def cycle_exists(request):
    """
    Returns a validator callback to ensure the cycle exists in the database
    """
    def validator(value):
        lz = get_localizer(request)
        (exists,) = (
            Session.query(
                Session.query(models.Cycle)
                .filter_by(id=value)
                .exists())
            .one())
        if not exists:
            raise Invalid(lz.translate(_(
                u'Specified a cycle that does not exist')))
        return value
    return validator


def unique_visit_cycle(request, patient, visit=None):
    """
    Returns a validator callback to ensure the cycle has not already been used

    TODO need a mechanism to check if the cycle can be repeated,
    for not just block all repetions, vaya con Dios...
    """
    def validator(value):
        lz = get_localizer(request)
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
