from nose.tools import with_setup
from sqlalchemy import Column, Integer

from occams.datastore.models import ModelClass, Modifiable

from tests import begin_func, rollback_func


Base = ModelClass('Base')


class ModifiableClass(Base, Modifiable):
    """
    Sample case of a class using ``Modifiable``'s functionality
    """
    __tablename__ = 'modifiable'
    id = Column(Integer, primary_key=True)


def setup_module():
    from tests import Session
    Base.metadata.create_all(Session.bind)


def teardown_module():
    from tests import Session
    Base.metadata.drop_all(Session.bind)


@with_setup(begin_func, rollback_func)
def test_modifiable_basic():
    """
    It should annotate the record with modification dates
    """
    from tests import Session
    from tests import assert_is_not_none

    record = ModifiableClass()
    Session.add(record)
    Session.flush()

    assert_is_not_none(record.create_date)
    assert_is_not_none(record.create_user_id)
    assert_is_not_none(record.modify_date)
    assert_is_not_none(record.modify_user_id)


@with_setup(begin_func, rollback_func)
def test_modifiable_invalid_date():
    """
    It should not allow use of inconsitent timelines
    """
    from tests import Session
    from tests import assert_raises
    import datetime
    from sqlalchemy.exc import IntegrityError

    record = ModifiableClass()
    Session.add(record)
    Session.flush()

    record.create_date += datetime.timedelta(1)
    with assert_raises(IntegrityError):
        Session.commit()


@with_setup(begin_func, rollback_func)
def test_modifable_non_existent_user():
    """
    It should fail if a non-existent user attemts to make a commti
    """
    from tests import Session
    from tests import assert_raises
    from occams.datastore.exc import NonExistentUserError

    # Clear any info set by setup function
    Session.remove()

    record = ModifiableClass()
    Session.add(record)

    with assert_raises(NonExistentUserError):
        Session.flush()
