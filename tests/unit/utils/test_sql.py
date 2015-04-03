from nose.tools import with_setup
from sqlalchemy import Column, Integer

from occams_datastore.models import ModelClass
from occams_datastore.utils.sql import JSON

from tests import Session, begin_func, rollback_func


@with_setup(begin_func, rollback_func)
def test_group_concat_single_value():
    """
    It should be able to handle a single value
    """
    from sqlalchemy import literal_column, cast, Unicode
    from tests import assert_items_equal
    from occams_datastore.utils.sql import group_concat

    data = (
        Session.query(
            cast(literal_column("'myitem'"), Unicode).label('name'),
            cast(literal_column("'foo'"), Unicode).label('value'))
        .subquery())

    query = (
        Session.query(group_concat(data.c.value, ';'))
        .select_from(data)
        .group_by(data.c.name))

    result, = query.one()
    assert_items_equal(['foo'], result.split(';'))


@with_setup(begin_func, rollback_func)
def test_group_concat_multi_value():
    """
    It should be able to delimit-multiple values
    """
    from sqlalchemy import literal_column, cast, Unicode
    from tests import assert_items_equal
    from occams_datastore.utils.sql import group_concat

    data = (
        Session.query(
            cast(literal_column("'myitem'"), Unicode).label('name'),
            cast(literal_column("'foo'"), Unicode).label('value'))
        .union(
            Session.query(
                cast(literal_column("'myitem'"), Unicode).label('name'),
                cast(literal_column("'bar'"), Unicode).label('value')))
        .subquery())

    query = (
        Session.query(group_concat(data.c.value, ';'))
        .select_from(data)
        .group_by(data.c.name))

    result, = query.one()
    assert_items_equal(['foo', 'bar'], result.split(';'))


@with_setup(begin_func, rollback_func)
def test_group_concat_sqlite_one_arg():
    """
    It should use SQLite's deafult arguments (comma delimiter)
    """
    from sqlalchemy import literal_column
    from tests import assert_items_equal
    from nose.plugins.skip import SkipTest
    from occams_datastore.utils.sql import group_concat

    if Session.bind.url.drivername != 'sqlite':
        raise SkipTest('Not using SQLite')

    data = (
        Session.query(
            literal_column("'myitem'").label('name'),
            literal_column("'foo'").label('value'))
        .union(
            Session.query(
                literal_column("'myitem'").label('name'),
                literal_column("'bar'").label('value')))
        .subquery())

    query = (
        Session.query(group_concat(data.c.value))
        .select_from(data)
        .group_by(data.c.name))

    result, = query.one()
    assert_items_equal(['foo', 'bar'], result.split(','))


@with_setup(begin_func, rollback_func)
def test_group_concat_sqlite_invalid_args():
    """
    It should only support at most two arguments in SQLite
    """
    from sqlalchemy import literal_column
    from tests import assert_raises
    from nose.plugins.skip import SkipTest
    from occams_datastore.utils.sql import group_concat

    if Session.bind.url.drivername != 'sqlite':
        raise SkipTest('Not using SQLite')

    data = (
        Session.query(
            literal_column("'myitem'").label('name'),
            literal_column("'foo'").label('value'))
        .union(
            Session.query(
                literal_column("'myitem'").label('name'),
                literal_column("'bar'").label('value')))
        .subquery())

    query = (
        Session.query(group_concat(data.c.value, ';', 'wtf'))
        .select_from(data)
        .group_by(data.c.name))

    with assert_raises(TypeError):
        result, = query.one()


@with_setup(begin_func, rollback_func)
def test_group_concat_postgresql_invalid_args():
    """
    It should only support at least two arguments in PostgreSQL
    """
    from sqlalchemy import literal_column
    from tests import assert_raises
    from nose.plugins.skip import SkipTest
    from occams_datastore.utils.sql import group_concat

    if Session.bind.url.drivername != 'postgresql':
        raise SkipTest('Not using PostgreSQL')

    data = (
        Session.query(
            literal_column("'myitem'").label('name'),
            literal_column("'foo'").label('value'))
        .union(
            Session.query(
                literal_column("'myitem'").label('name'),
                literal_column("'bar'").label('value')))
        .subquery())

    query = (
        Session.query(group_concat(data.c.value))
        .select_from(data)
        .group_by(data.c.name))

    with assert_raises(TypeError):
        result, = query.one()


@with_setup(begin_func, rollback_func)
def test_to_date():
    """
    It should be able to cast to a date
    """
    import datetime
    from sqlalchemy import literal_column
    from tests import assert_equals
    from occams_datastore.utils.sql import to_date

    expected = datetime.date(1976, 7, 4)
    query = (
        Session.query(
            to_date(literal_column("'%s'" % expected)).label('value')))

    result, = query.one()
    assert_equals(str(expected), str(result))


@with_setup(begin_func, rollback_func)
def test_to_datetime():
    """
    It should be able to cast to a datetime
    """
    import datetime
    from sqlalchemy import literal_column
    from tests import assert_equals
    from occams_datastore.utils.sql import to_datetime

    expected = datetime.datetime(1976, 7, 4, 5, 0)
    query = (
        Session.query(
            to_datetime(literal_column("'%s'" % expected)).label('value')))

    result, = query.one()
    assert_equals(str(expected), str(result))


Base = ModelClass('Base')


class SomeMapping(Base):
    __tablename__ = 'somemapping'
    id = Column(Integer, primary_key=True)
    value = Column(JSON)


def setup_module():
    Base.metadata.create_all(Session.bind)


def teardown_module():
    Base.metadata.drop_all(Session.bind)


@with_setup(begin_func, rollback_func)
def test_json():
    """
    It should be able to marshall JSON data
    """
    from tests import assert_is_none, assert_dict_equal

    Session.add(SomeMapping(value=None))
    record = Session.query(SomeMapping).one()
    assert_is_none(record.value)

    some_json_value = record.value = {
        'foo': 'some val',
        'bar': 420}
    Session.flush()

    # Clear all session objects so that they can be reloaded
    Session.expunge_all()

    record = Session.query(SomeMapping).one()
    assert_dict_equal(some_json_value, record.value)


@with_setup(begin_func, rollback_func)
def test_json_native_postgresql():
    """
    It should use PostgreSQL's native JSON implementation
    """
    from tests import assert_equals
    from nose.plugins.skip import SkipTest

    if Session.bind.url.drivername != 'postgresql':
        raise SkipTest('Not using PostgreSQL')

    assert_equals(SomeMapping.value.type.compile(Session.bind.dialect), 'JSON')
