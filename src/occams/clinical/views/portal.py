import colander
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from sqlalchemy import func, orm, sql
import transaction

from occams.datastore import model as datastore

from .. import _, log, models, Session


@view_config(
    route_name='clinical',
    permission='view',
    renderer='occams.clinical:templates/portal/home.pt')
def home(request):
    layout = request.layout_manager.layout
    layout.title = _(u'Welcome to OCCAMS!')

    recent_query = search_recent()
    return {
        'recent_list': recent_query,
        'recent_count': recent_query.count() }


def search_recent():
    """
    Searches for recent patients
    """
    return (
        Session.query(models.Patient)
        .add_column(
            func.greatest(
                (Session.query(models.Visit.visit_date)
                    .filter_by(patient_id=models.Patient.id)
                    .order_by(models.Visit.visit_date.desc())
                    .limit(1)
                    .correlate(models.Patient)
                    .as_scalar()),
                models.Patient.modify_date,
                ).label('access_date'))
        .order_by(
            'access_date DESC',
            models.Patient.our.asc())
        .limit(10))





