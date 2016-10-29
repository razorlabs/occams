from pyramid.view import view_config
import sqlalchemy as sa
import wtforms

from .. import models
from ..renderers import form2json, version2json
from ..utils.forms import Form


@view_config(
    route_name='studies.settings',
    permission='admin',
    renderer='../templates/settings/view.pt')
def view(context, request):
    return {}


# TODO: cleverly join this with the other available_schmata running around
@view_config(
    route_name='studies.settings',
    permission='admin',
    xhr=True,
    request_param='vocabulary=available_schemata',
    renderer='json')
def available_schemata(context, request):
    """
    Returns a listing of available schemata for the study

    The results will try to exclude schemata configured for patients,
    or schemata that is currently used by the context study (if editing).

    GET parameters:
        term -- (optional) filters by schema title or publish date
        schema -- (optional) only shows results for specific schema name
                  (useful for searching for a schema's publish dates)
        grouped -- (optional) groups all results by schema name
    """
    dbsession = request.dbsession

    class SearchForm(Form):
        term = wtforms.StringField()
        schema = wtforms.StringField()
        grouped = wtforms.BooleanField()

    form = SearchForm(request.GET)
    form.validate()

    query = (
        dbsession.query(models.Schema)
        .filter(models.Schema.publish_date != sa.null())
        .filter(models.Schema.retract_date == sa.null())
        .filter(~models.Schema.name.in_(
            # Exclude study forms
            dbsession.query(models.Schema.name)
            .join(models.study_schema_table)
            .union(
                # Exclude randomzation forms
                dbsession.query(models.Schema.name)
                .join(models.Study.randomization_schema),

                # Exclude termination forms
                dbsession.query(models.Schema.name)
                .join(models.Study.termination_schema),

                # Exclude already selected patient forms
                dbsession.query(models.Schema.name)
                .join(models.patient_schema_table))
            .correlate(None)
            .subquery())))

    if form.schema.data:
        query = query.filter(models.Schema.name == form.schema.data)

    if form.term.data:
        wildcard = u'%' + form.term.data + u'%'
        query = query.filter(
            models.Schema.title.ilike(wildcard)
            | sa.cast(models.Schema.publish_date,
                      sa.Unicode).ilike(wildcard))

    query = (
        query.order_by(
            models.Schema.title,
            models.Schema.publish_date.asc())
        .limit(100))

    return {
        '__query__': form.data,
        'schemata': (form2json(query)
                     if form.grouped.data
                     else [version2json(i) for i in query])
    }
