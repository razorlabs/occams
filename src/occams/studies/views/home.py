from good import *  # NOQA
from pyramid.view import view_config

from .. import models, Session
from . import study as study_views


@view_config(
    route_name='home',
    permission='view',
    renderer='../templates/home/view.pt')
def home(request):
    studies_query = (
        Session.query(models.Study)
        .order_by(models.Study.title.asc()))

    modified_query = (
        Session.query(models.Patient)
        .order_by(models.Patient.modify_date.desc())
        .limit(10))

    viewed = sorted((request.session.get('viewed') or {}).values(),
                    key=lambda v: v['view_date'],
                    reverse=True)

    studies_data = [study_views.view_json(s, request, deep=False)
                    for s in studies_query]

    return {
        'studies_data': studies_data,
        'studies_count': len(studies_data),

        'modified': modified_query,
        'modified_count': modified_query.count(),

        'viewed': viewed,
        'viewed_count': len(viewed),
    }
