from nose.tools import with_setup

from sqlalchemy import Column, Integer
from sqlalchemy.orm import scoped_session, sessionmaker

from occams.datastore.models import ModelClass, Modifiable


Session = scoped_session(sessionmaker())

Base = ModelClass('Base')


class ModifiableClass(Base, Modifiable):
    """
    Sample case of a class using ``Modifiable``'s functionality
    """
    __tablename__ = 'modifiable'
    id = Column(Integer, primary_key=True)


def setup_modifiable():
    """
    Create sandbox for a database that would be using modifiable
    """
    from sqlalchemy import create_engine
    from occams.datastore.models import DataStoreModel
    from occams.datastore.models.events import register
    Session.configure(bind=create_engine('sqlite://'),
                      info={'user': 'bitcore@ucsd.edu'})
    register(Session)
    DataStoreModel.metadata.create_all(Session.bind)
    Base.metadata.create_all(Session.bind)


def teardown_modifiable():
    from occams.datastore.models import DataStoreModel
    DataStoreModel.metadata.drop_all(Session.bind)
    Base.metadata.drop_all(Session.bind)
    Session.remove()


@with_setup(setup_modifiable, teardown_modifiable)
def test_modifiable_basic():
    """
    It should annotate the record with modification dates
    """
    from nose.tools import assert_is_not_none
    from occams.datastore.models import User
    Session.add(User(key=u'bitcore@ucsd.edu'))
    Session.commit()

    record = ModifiableClass()
    Session.add(record)
    Session.commit()

    assert_is_not_none(record.create_date)
    assert_is_not_none(record.create_user_id)
    assert_is_not_none(record.modify_date)
    assert_is_not_none(record.modify_user_id)


@with_setup(setup_modifiable, teardown_modifiable)
def test_modifiable_invalid_date():
    """
    It should not allow use of inconsitent timelines
    """
    from nose.tools import assert_raises
    import datetime
    from sqlalchemy.exc import IntegrityError
    from occams.datastore.models import User
    Session.add(User(key=u'bitcore@ucsd.edu'))
    Session.commit()

    record = ModifiableClass()
    Session.add(record)
    Session.commit()

    record.create_date += datetime.timedelta(1)
    with assert_raises(IntegrityError):
        Session.commit()


@with_setup(setup_modifiable, teardown_modifiable)
def test_modifable_non_existent_user():
    """
    It should fail if a non-existent user attemts to make a commti
    """
    from nose.tools import assert_raises
    from occams.datastore.exc import NonExistentUserError

    record = ModifiableClass()
    Session.add(record)

    with assert_raises(NonExistentUserError):
        Session.commit()
