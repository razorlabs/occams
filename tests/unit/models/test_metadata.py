import pytest

from sqlalchemy import Column, Integer
from occams_datastore.models import ModelClass, Modifiable


Base = ModelClass('Base')


class ModifiableClass(Base, Modifiable):
    """
    Sample case of a class using ``Modifiable``'s functionality

    We define this outside of a fixture to let SQLalchemy fully
    evaluate all modules (otheriwise pytest get's stuck indefinitely)
    """
    __tablename__ = 'modifiable'
    id = Column(Integer, primary_key=True)


@pytest.fixture(autouse=True, scope='module')
def create_tables(request, engine):
    Base.metadata.create_all(engine)

    def drop_tables():
        Base.metadata.drop_all(engine)

    request.addfinalizer(drop_tables)


def test_modifiable_basic(db_session):
    """
    It should annotate the record with modification dates
    """

    record = ModifiableClass()
    db_session.add(record)
    db_session.flush()

    assert record.create_date is not None
    assert record.create_user_id is not None
    assert record.modify_date is not None
    assert record.modify_user_id is not None


def test_modifiable_invalid_date(db_session):
    """
    It should not allow use of inconsitent timelines
    """
    import datetime
    from sqlalchemy.exc import IntegrityError

    record = ModifiableClass()
    db_session.add(record)
    db_session.flush()

    record.create_date += datetime.timedelta(1)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_modifable_non_existent_user(db_session):
    """
    It should fail if a non-existent user attemts to make a commti
    """

    db_session.info = {}

    record = ModifiableClass()
    db_session.add(record)

    with pytest.raises(AssertionError) as excinfo:
        db_session.flush()

    assert 'not configured' in str(excinfo.value)
