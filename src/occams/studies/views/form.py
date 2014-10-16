import collections
from itertools import groupby

from good import *  # NOQA
from pyramid.httpexceptions import HTTPBadRequest, HTTPOk
from pyramid.session import check_csrf_token
from pyramid.view import view_config

from .. import _, models, Session
from ..validators import invalid2dict, Model


#
# TODO, update patient on form changes
#

def version2json(schema):
    """
    Returns a single schema json record
    (this is how it's stored in the database)
    """
    return {
        'id': schema.id,
        'name': schema.name,
        'title': schema.title,
        'publish_date': schema.publish_date.isoformat()}


def form2json(schemata):
    """
    Returns a representation of schemata grouped by versions.

    This is useful for representing schemata grouped by their version.

    The final dict contains the following values:
        ``schema`` -- a dict containing:
            ``name`` -- the schema name
            ``title`` -- the schema's most recent human title
        ``versions`` -- a list containining each version (see ``version2json``)

    This method accepts a single value (in which it will be transformted into
    a schema/versions pair, or a list which will be regrouped
    into schema/versions pairs
    """

    def by_name(schema):
        return schema.name

    def by_version(schema):
        return schema.publish_date

    def make_json(groups):
        groups = sorted(groups, key=by_version)
        return {
            'schema': {
                'name': groups[0].name,
                'title': groups[-1].title
                },
            'versions': list(map(version2json, groups))
            }

    if isinstance(schemata, collections.Iterable):
        schemata = sorted(schemata, key=by_name)
        return [make_json(g) for k, g in groupby(schemata, by_name)]
    elif isinstance(schemata, models.Schema):
        return make_json([schemata])


@view_config(
    route_name='forms',
    permission='add',
    request_method='POST',
    renderer='json')
def add_json(context, request):
    check_csrf_token(request)

    def check_study_form(value):
        query = (
            Session.query(models.Visit)
            .filter(models.Visit.id == context.__parent__.id)
            .join(models.Visit.cycles)
            .join(models.Cycle.study)
            .filter(
                models.Cycle.schemata.any(id=value.id)
                | models.Study.schemata.any(id=value.id)))
        (exists,) = Session.query(query.exists()).one()
        if not exists:
            raise Invalid(request.localizer.translate(
                _('${schema} is not part of the studies for this visit'),
                mapping={'schema': value.title}))
        return value

    schema = Schema({
        'schemata': [All(
            Model(models.Schema, localizer=request.localizer),
            check_study_form)],
        Extra: object})

    try:
        data = schema(request.json_body)
    except Invalid as e:
        raise HTTPBadRequest(json={'errors': invalid2dict(e)})

    default_state = (
        Session.query(models.State)
        .filter_by(name='pending-entry')
        .one())

    for schema in data['schemata']:
        entity = models.Entity(
            schema=schema,
            collect_date=context.__parent__.visit_date,
            state=default_state)
        context.__parent__.entities.add(entity)
        context.__parent__.patient.entities.add(entity)

    Session.flush()

    return HTTPOk()


@view_config(
    route_name='forms',
    permission='delete',
    request_method='DELETE',
    renderer='json')
def delete_json(context, request):
    """
    Deletes forms in bulk
    """
    check_csrf_token(request)

    schema = Schema({
        'forms': [Model(
            models.Entity,
            msg=_(u'Form does not exist'),
            localizer=request.localizer)],
        Extra: Remove})

    try:
        data = schema(request.json_body)
    except Invalid as e:
        raise HTTPBadRequest(json={'errors': invalid2dict(e)})

    entity_ids = [entity.id for entity in data['forms']]

    (Session.query(models.Entity)
        .filter(models.Entity.id.in_(
            Session.query(models.Context.entity_id)
            .filter(models.Context.entity_id.in_(entity_ids))
            .filter(models.Context.external == u'visit')
            .filter(models.Context.key == context.__parent__.id)))
        .delete('fetch'))

    Session.flush()

    return HTTPOk()
