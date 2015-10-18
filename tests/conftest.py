import pytest


@pytest.fixture(autouse=True, scope='session')
def create_tables():
    """
    Intialize the connection for this module
    """
    from sqlalchemy import create_engine
    from occams_roster import Session, models
    Session.configure(bind=create_engine('sqlite:///:memory:'))
    models.Base.metadata.create_all(Session.bind)


@pytest.yield_fixture
def config():
    from pyramid import testing
    config = testing.setUp()
    yield config
    testing.tearDown()


@pytest.yield_fixture()
def db_session():
    import transaction
    from occams_roster import Session
    yield Session
    transaction.abort()
    Session.remove()
