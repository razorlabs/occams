from pyramid.httpexceptions import HTTPBadRequest, HTTPForbidden
from pyramid.session import check_csrf_token
from pyramid.view import view_config
import six
from slugify import slugify
import wtforms

from occams.utils.forms import wtferrors, Form
from occams_forms.renderers import form2json

from .. import _, models


@view_config(
    route_name='studies.cycle',
    permission='view',
    xhr=True,
    renderer='json')
def view_json(context, request):
    cycle = context
    return {
        '__url__': request.route_path('studies.cycle',
                                      study=cycle.study.name,
                                      cycle=cycle.name),
        'id': cycle.id,
        'name': cycle.name,
        'title': cycle.title,
        'week': cycle.week,
        'is_interim': cycle.is_interim,
        'forms': form2json(cycle.schemata)
        }


@view_config(
    route_name='studies.cycles',
    permission='add',
    request_method='POST',
    xhr=True,
    renderer='json')
@view_config(
    route_name='studies.cycle',
    permission='edit',
    request_method='PUT',
    xhr=True,
    renderer='json')
def edit_json(context, request):
    check_csrf_token(request)
    db_session = request.db_session

    form = CycleSchema(context, request).from_json(request.json_body)

    if not form.validate():
        raise HTTPBadRequest(json={'errors': wtferrors(form)})

    if isinstance(context, models.CycleFactory):
        cycle = models.Cycle(study=context.__parent__)
        db_session.add(cycle)
    else:
        cycle = context

    cycle.name = six.text_type(slugify(form.title.data))
    cycle.title = form.title.data
    cycle.week = form.week.data
    cycle.is_interim = form.is_interim.data

    db_session.flush()

    return view_json(cycle, request)


@view_config(
    route_name='studies.cycle',
    permission='delete',
    request_method='DELETE',
    xhr=True,
    renderer='json')
def delete_json(context, request):
    check_csrf_token(request)
    db_session = request.db_session

    (has_visits,) = (
        db_session.query(
            db_session.query(models.Visit)
            .filter(models.Visit.cycles.any(id=context.id))
            .exists())
        .one())

    if has_visits and not request.has_permission('admin', context):
        raise HTTPForbidden(_(u'Cannot delete a cycle with visits'))

    db_session.delete(context)
    db_session.flush()

    return {
        '__next__': request.route_path(
            'studies.study', study=context.study.name),
        'message': _(u'Successfully removed "${cycle}"',
                     mapping={'cycle': context.title})
        }


def CycleSchema(context, request):
    db_session = request.db_session

    def check_unique_url(form, field):
        slug = six.text_type(slugify(field.data))
        query = db_session.query(models.Cycle).filter_by(name=slug)
        if isinstance(context, models.Cycle):
            query = query.filter(models.Cycle.id != context.id)
        (exists,) = db_session.query(query.exists()).one()
        if exists:
            raise wtforms.ValidationError(request.localizer.translate(_(
                u'Does not yield a unique URL.')))

    class CycleForm(Form):
        title = wtforms.StringField(
            validators=[
                wtforms.validators.InputRequired(),
                wtforms.validators.Length(min=3, max=32),
                check_unique_url])
        week = wtforms.IntegerField()
        is_interim = wtforms.BooleanField()

    return CycleForm
