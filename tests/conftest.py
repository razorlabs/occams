import pytest


@pytest.fixture(autouse=True, scope='session')
def engine():
    """
    Intialize the connection for this module
    """
    from sqlalchemy import create_engine
    from occams_roster import models
    engine = create_engine('sqlite:///:memory:')
    models.Base.metadata.create_all(engine)
    return engine


@pytest.yield_fixture
def config():
    from pyramid import testing
    config = testing.setUp()
    yield config
    testing.tearDown()


@pytest.yield_fixture()
def db_session(engine):
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
