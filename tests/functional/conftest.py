"""
Fixtures for end-to-end testing of application url endpoints
"""

import pytest

from tests.conftest import USERID

@pytest.fixture(scope='session')
def app(request):
    """
    Sets up a full-stacked singleton WSGI app

    :param request: The pytest context

    :returns: a WSGI application
    """
    import tempfile
    import shutil
    from configparser import ConfigParser
    from occams import main

    # The pyramid_who plugin requires a who file, so let's create a
    # barebones files for it...
    who_ini = tempfile.NamedTemporaryFile(mode='w')
    who = ConfigParser()
    who.add_section('general')
    who.set('general', 'request_classifier',
            'repoze.who.classifiers:default_request_classifier')
    who.set('general', 'challenge_decider',
            'repoze.who.classifiers:default_challenge_decider')
    who.set('general', 'remote_user_key', 'REMOTE_USER')
    who.write(who_ini)
    who_ini.flush()

    db_url = request.config.getoption('--db')
    redis_url = request.config.getoption('--redis')

    tmp_dir = tempfile.mkdtemp()

    _app = main({}, **{
        'redis.url': redis_url,
        'redis.sessions.url': redis_url,
        'redis.sessions.prefix': 'occams-session:',
        'redis.sessions.timeout': 36000,
        'redis.sessions.secret': 'sekrit',

        'who.config_file': who_ini.name,
        'who.identifier_id': '',

        'webassets.debug': True, # Don't build assets

        'sqlalchemy.url': db_url,
        'occams.groups': [],

        'celery.broker.url': redis_url,
        'celery.backend.url': redis_url,
        'celery.blame': 'celery@localhost',

        'studies.export.dir': '/tmp',
        'studies.export.plans': [
            'occams.exports.pid.PidPlan',
            'occams.exports.enrollment.EnrollmentPlan',
            'occams.exports.visit.VisitPlan',
            'occams.exports.schema.SchemaPlan.list_all',
        ],
        'studies.pid.package': 'occams',
        'studies.blob.dir': '/tmp',
    })

    who_ini.close()

    yield _app

    shutil.rmtree(tmp_dir)


@pytest.fixture(scope='session')
def testapp(request, app, using_dbsession):
    """
    Initiates a user request against a WSGI stack

    :param request: The pytest context
    :param wsgi: An initialized WSGI stack
    :param dbsession: A database session for seting up pre-existing data

    :returns: a test app request against the WSGI instance
    """
    from webtest import TestApp
    from occams import models
    from occams.models.meta import Base

    with using_dbsession(app) as dbsession:
        dbsession.add_all([
            models.User(key=USERID),
            models.State(name='pending-entry', title='Pending Entry'),
            models.State(name='pending-review', title='Pending Review'),
            models.State(name='pending-correction', title='Pending Correction'),
            models.State(name='complete', title='Complete')
        ])

    _testapp = TestApp(app)
    yield _testapp


@pytest.fixture(scope='session')
def using_dbsession(request):
    """
    Helper fixture to create a transaction-scoped database session during setup

    It is highly recommended that this fixture not be used in an actaul test
    as the tests should just be concerned with fetching endpoints
    """
    import contextlib

    @contextlib.contextmanager
    def _make_transaction(app):
        import transaction
        from occams.models import get_tm_session, set_pg_locals

        with transaction.manager:
            dbsession = get_tm_session(
                app.registry['dbsession_factory'],
                transaction.manager
            )
            set_pg_locals(dbsession, 'pytest', USERID)

            yield dbsession

    return _make_transaction


@pytest.fixture(autouse=True)
def dbtruncate(request, app, using_dbsession):
    """
    Truncate data after each test run
    """

    from zope.sqlalchemy import mark_changed

    def truncate():
        with using_dbsession(app) as dbsession:
            # DELETE is dramatically faster than TRUNCATE
            # http://stackoverflow.com/a/11423886/148781
            # We also have to do this as a raw query becuase SA does
            # not have a way to invoke server-side cascade
            dbsession.execute('DELETE FROM "identifier" CASCADE')
            dbsession.execute('DELETE FROM "rostersite" CASCADE')
            dbsession.execute('DELETE FROM "study" CASCADE')
            dbsession.execute('DELETE FROM "patient" CASCADE')
            dbsession.execute('DELETE FROM "site" CASCADE')
            dbsession.execute('DELETE FROM "schema" CASCADE')
            dbsession.execute('DELETE FROM "export" CASCADE')
            # Don't truncate accounts or states since those should never change for these tests
            mark_changed(dbsession)

    request.addfinalizer(truncate)
