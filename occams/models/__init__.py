from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker, configure_mappers
import zope.sqlalchemy

# import or define all models here to ensure they are attached to the
# Base.metadata prior to any initialization routines

from .roster import Site as RosterSite, Identifier  # noqa

from .studies import (  # noqa
    study_schema_table,
    cycle_schema_table,
    patient_schema_table,
    termination_schema_table,
    visit_cycle_table,
    StudyFactory,
    Study,
    CycleFactory,
    Cycle,
    Arm,
    Stratum,
    ExternalServiceFactory,
    ExternalService,
    SiteFactory,
    Site,
    PatientFactory,
    Patient,
    ReferenceTypeFactory,
    ReferenceType,
    PatientReference,
    EnrollmentFactory,
    Enrollment,
    VisitFactory,
    Visit,
    ExportFactory,
    Export,
    EntryFactory,
    Survey,
    SurveyFactory
)

from .forms import (  # noqa
    FormFactory,
    Form,
    VersionFactory,
    AttributeFactory
)

from .schema import (  # noqa
    Schema,
    Category,
    Attribute,
    Choice
)

from .metadata import User  # noqa

from .storage import (  # noqa
    State,
    Context,
    Entity,
    EntityAttachment,
    EntityAttachmentBlob,
    HasEntities,
)

# run configure_mappers after defining all of the models to ensure
# all relationships can be setup
configure_mappers()


def get_engine(settings, prefix='sqlalchemy.'):
    return engine_from_config(settings, prefix)


def get_session_factory(engine):
    factory = sessionmaker()
    factory.configure(bind=engine)
    return factory


def get_tm_session(session_factory, transaction_manager):
    """
    Get a ``sqlalchemy.orm.Session`` instance backed by a transaction.

    This function will hook the session to the transaction manager which
    will take care of committing any changes.

    - When using pyramid_tm it will automatically be committed or aborted
      depending on whether an exception is raised.

    - When using scripts you should wrap the session in a manager yourself.
      For example::

          import transaction

          engine = get_engine(settings)
          session_factory = get_session_factory(engine)
          with transaction.manager:
              dbsession = get_tm_session(session_factory, transaction.manager)

    """

    dbsession = session_factory()

    zope.sqlalchemy.register(
        dbsession, transaction_manager=transaction_manager)

    return dbsession


def includeme(config):
    """
    Initialize the model for a Pyramid app.

    Activate this setup using ``config.include('occams.models')``.

    """
    settings = config.get_settings()

    # use pyramid_tm to hook the transaction lifecycle to the request
    config.include('pyramid_tm')

    session_factory = get_session_factory(get_engine(settings))
    config.registry['dbsession_factory'] = session_factory

    # make request.dbsession available for use in Pyramid
    config.add_request_method(
        # r.tm is the transaction manager used by pyramid_tm
        lambda r: get_tm_session(session_factory, r.tm),
        'dbsession',
        reify=True
    )
