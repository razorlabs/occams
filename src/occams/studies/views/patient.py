from datetime import datetime
from pyramid.httpexceptions import (
    HTTPBadRequest, HTTPForbidden, HTTPFound, HTTPNotFound)
from pyramid.view import view_config
from sqlalchemy import func, orm, sql
import wtforms.fields.html5
import wtforms.widgets.html5

from .. import _, models, Session
from ..widgets.pager import Pager


@view_config(
    route_name='patients',
    permission='patient_view',
    request_method='q',
    renderer='../templates/patient/search.pt')
def search(request):
    search_term = request.GET.get('q')

    if not search_term:
        return {}

    current_page = int(request.GET.get('page', 0))
    search_query = query_by_ids(search_term)
    search_count = search_query.count()
    pager = Pager(current_page, 10, search_count)
    return {'pager': pager}


@view_config(
    route_name='patient',
    permission='patient_view',
    renderer='../templates/patient/view.pt')
def view(request):
    # TODO: Only include the sites the user is a member of
    #sites_query = Session.query(models.Site).order_by(models.Site.title)
    #reference_types_query = (
        #Session.query(models.ReferenceType)
        #.order_by(models.ReferenceType.title))
    #edit_form = PatientForm()
    #edit_form.site.choices = [(s.id, s.title) for s in sites_query]
    #import pdb; pdb.set_trace()
    #edit_form.references.reference_type.choices = \
        #[(r.id, r.title) for r in reference_types_query]
    data = get_patient_data(request, get_patient(request))
    data.update({
    })
    return data

@view_config(
    route_name='patient',
    permission='patient_view',
    request_param='alt=json',
    renderer='json')
@view_config(
    route_name='patient',
    permission='patient_view',
    xhr=True,
    renderer='json')
def view_json(request):
    return get_patient_data(request, get_patient(request))


def get_patient_data(request, patient):
    p = patient
    return {
        'patient': {
            '__src__': request.route_path('patient', patient=p.pid),
            'id': p.id,
            'site': {'name': p.site.name, 'title': p.site.title},
            'pid': p.pid,
            'references': [{
                'reference_type': {
                    'name': r.reference_type.name,
                    'title': r.reference_type.title
                    },
                'reference_number': r.reference_number,
                } for r in p.references],
            'enrollments': [{
                'study': {
                    'name': e.study.name,
                    'title': e.study.title,
                    'is_blinded': e.study.is_blinded
                    },
                'consent_date': e.consent_date.isoformat(),
                'latest_consent_date': e.latest_consent_date.isoformat(),
                'termination_date': (
                    e.termination_date and e.termination_date.isoformat()),
                'reference_number': e.reference_number,
                'stratum': e.stratum and {
                    'randid': e.stratum.randid,
                    'arm': None if e.study.is_blinded else {
                        'name': e.stratum.arm.name,
                        'title': e.stratum.arm.title,
                        }
                    }
                } for e in p.enrollments],
            'visits': [{
                'cycles': [{
                    'study': {
                        'name': c.study.name,
                        'title': c.study.title,
                        'code': c.study.code
                        },
                    'name': c.name,
                    'title': c.title,
                    'week': c.week
                    } for c in v.cycles],
                'visit_date': v.visit_date.isoformat(),
                'num_complete': len([e for e in v.entities
                                     if e.state.name == 'complete']),
                'total_forms': len(v.entities),
                } for v in p.visits],
            'modify_date': p.modify_date.isoformat(),
            'modify_user': p.modify_user.key,
            'create_date': p.create_date.isoformat(),
            'create_user': p.create_user.key
            }
        }


def get_patient(request):
    """
    Uses the URL dispatch matching dictionary to find a study
    """
    try:
        patient = (
            Session.query(models.Patient)
            .filter_by(pid=request.matchdict['patient']).one())
        request.session.setdefault('viewed', {})
        request.session['viewed'][patient.pid] = {
            'pid': patient.pid,
            'view_date': datetime.now()
        }
        request.session.changed()
        return patient
    except orm.exc.NoResultFound:
        raise HTTPNotFound


def query_by_ids(term):
    """
    Search utility that returns a patient entry query based on reference numbers
    """
    wildcard = '%{0}%'.format(term)
    return (
        Session.query(models.Patient)
        .outerjoin(models.Patient.enrollments)
        .outerjoin(models.Patient.strata)
        .outerjoin(models.Patient.reference_numbers)
        .filter(or_(
            models.Patient.pid.ilike(wildcard),
            models.Enrollment.reference_number.ilike(wildcard),
            models.Stratum.reference_number.ilike(wildcard),
            models.PatientReference.reference_number.ilike(wildcard),
            models.Patient.initials.ilike(wildcard)))
        .order_by(models.Patient.pid.asc()))


#class ReferenceForm(wtforms.Form):

    #reference_type = wtforms.SelectField()

    #reference_number = wtforms.StringField()


#class PatientForm(wtforms.Form):

    #site = wtforms.SelectField()

    #references = wtforms.FieldList(wtforms.FormField(ReferenceForm))
