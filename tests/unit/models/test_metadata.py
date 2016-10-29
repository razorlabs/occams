import pytest

from sqlalchemy import Column, Integer, MetaData
from occams_datastore.models import Base, Modifiable


class TestModel(Base):
    __abstract__ = True
    metadata = MetaData()


class ModifiableClass(TestModel, Modifiable):
    """
    Sample case of a class using ``Modifiable``'s functionality

    We define this outside of a fixture to let SQLalchemy fully
    evaluate all modules (otheriwise pytest get's stuck indefinitely)
    """
    __tablename__ = 'modifiable'
    id = Column(Integer, primary_key=True)


@pytest.fixture(autouse=True, scope='module')
def create_tables(request, engine):
    TestModel.metadata.create_all(engine)

    def drop_tables():
        TestModel.metadata.drop_all(engine)

    request.addfinalizer(drop_tables)


def test_modifiable_basic(dbsession):
    """
    It should annotate the record with modification dates
    """

    record = ModifiableClass()
    dbsession.add(record)
    dbsession.flush()

    assert record.create_date is not None
    assert record.create_user_id is not None
    assert record.modify_date is not None
    assert record.modify_user_id is not None


def test_modifiable_invalid_date(dbsession):
    """
    It should not allow use of inconsitent timelines
    """
    import datetime
    from sqlalchemy.exc import IntegrityError

    record = ModifiableClass()
    dbsession.add(record)
    dbsession.flush()

    record.create_date += datetime.timedelta(1)
    with pytest.raises(IntegrityError):
        dbsession.flush()


def test_modifable_non_existent_user(dbsession):
    """
    It should fail if a non-existent user attemts to make a commti
    """

    dbsession.info = {}

    record = ModifiableClass()
    dbsession.add(record)

    with pytest.raises(AssertionError) as excinfo:
        dbsession.flush()

    assert 'not configured' in str(excinfo.value)
