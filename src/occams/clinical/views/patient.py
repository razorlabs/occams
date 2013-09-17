import colander
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from sqlalchemy import func, orm, sql
import transaction

from occams.datastore import model as datastore

from .. import _, log, models, Session


def search_by_content(terms, with_phi=False):
    """
    Search utility that returns a patient entry query from based on string searching
    """
    terms = [t.lower() for t in terms]

    # "macro" function to build an OUR number query from a session
    build_query = lambda session: (
        session.query (models.Patient.our)
        .filter(models.Patient.site.has(zid=site_zid))
        .filter(
            or_(*map(lambda t: models.Patient.our.ilike('%%%s%%' % t), terms))
            | or_(*map(lambda t: models.Patient.legacy_number.ilike('%%%s%%' % t), terms))
            | or_(*map(lambda t: models.Patient.initials.ilike('%%%s%%' % t), terms))
            | models.Patient.enrollments.any(
                or_(*map(lambda t: models.Enrollment.reference_number.ilike('%%%s%%' % t), terms))
                )
            | models.Patient.reference_numbers.any(
                or_(*map(lambda t: models.PatientReference.reference_number.ilike('%%%s%%' % t), terms))
                )
            )
        .union(
            session.query(models.Patient.our)
            .filter(models.Patient.site.has(zid=site_zid))
            .join(datastore.Context,
                (datastore.Context.key == models.Patient.id)
                & (datastore.Context.external == 'patient')
                )
            .filter(models.Context.entity.has(
                datastore.Entity._string_values.any(
                    or_(*map(lambda t: datastore.ValueString._value.ilike('%%%s%%' % t), terms))
                    )
                | datastore.Entity._integer_values.any(
                    sql.cast(datastore.ValueInteger._value, types.Unicode).in_(terms)
                    )
                )),

            session.query(models.Patient.our)
            .filter(models.Patient.site.has(zid=site_zid))
            .join(datastore.Context,
                (datastore.Context.key == models.Patient.id)
                & (datastore.Context.external == 'patient')
                )
            .join(datastore.ValueObject,
                datastore.ValueObject.entity_id == datastore.Context.entity_id
                )
            .join(datastore.Entity,
                datastore.Entity.id == datastore.ValueObject._value
                )
            .filter(
                datastore.Entity._string_values.any(
                    *map(lambda t: datastore.ValueString._value.ilike('%%%s%%' % t), terms)
                    )
                | datastore.Entity._integer_values.any(
                    sql.cast(datastore.ValueInteger._value, types.Unicode).in_(terms)
                    )
                )
            )
        )

    our_number_query = build_query(FiaSession)

    if with_phi:
        our_number_query = our_number_query.union(
            FiaSession.query(models.Patient.our)
            .filter(models.Patient.site.has(zid=site_zid))
            .filter(models.Patient.our.in_(
                # can't do cross-database querying, so we must build the phi listing
                set([r.our for r in build_query(PhiSession)])
                ))
            )

    # the final result set (correlated subquery)
    return (
        FiaSession.query(models.Patient)
        .filter(models.Patient.site.has(zid=site_zid))
        .filter(models.Patient.our.in_(our_number_query.subquery()))
        )


def search_by_ids(term):
    """
    Search utility that returns a patient entry query based on reference numbers
    """
    return (
        Session.query(models.Patient)
        .filter(
            models.Patient.our == term
            | models.Patient.legacy_number == term
            | models.Patient.enrollments.any(reference_number=term)
            | models.Patient.strata.any(reference_number=term)
            | models.Patient.reference_numbers.any(reference_number=term)
            | models.Patient.initials.ilike('%{0}%'.format(term))))


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


@view_config(
    route_name='home',
    permission='view',
    renderer='occams.clinical:templates/patient/home.pt')
def home(request):
    request.layout_manager.layout.content_title = _(u'Welcome to OCCAMS!')
    recent_query = search_recent()

    return {
        'recent_count': recent_query.count(),
        'recent_list': recent_query}




