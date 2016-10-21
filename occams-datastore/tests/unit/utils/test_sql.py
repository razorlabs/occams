import pytest

from sqlalchemy import Column, Integer, MetaData

from occams_datastore.models import Base
from occams_datastore.utils.sql import JSON


class TestModel(Base):
    __abstract__ = True
    metadata = MetaData()


class SomeMapping(TestModel):
    """
    We define this outside of a fixture to let SQLalchemy fully
    evaluate all modules (otheriwise pytest get's stuck indefinitely)
    """
    __tablename__ = 'somemapping'
    id = Column(Integer, primary_key=True)
    value = Column(JSON)


@pytest.fixture(autouse=True, scope='module')
def create_tables(request, engine):
    TestModel.metadata.create_all(engine)

    def drop_tables():
        TestModel.metadata.drop_all(engine)

    request.addfinalizer(drop_tables)


def test_group_concat_single_value(db_session):
    """
    It should be able to handle a single value
    """
    from sqlalchemy import literal_column, cast, Unicode
    from occams_datastore.utils.sql import group_concat

    data = (
        db_session.query(
            cast(literal_column("'myitem'"), Unicode).label('name'),
            cast(literal_column("'foo'"), Unicode).label('value'))
        .subquery())

    query = (
        db_session.query(group_concat(data.c.value, ';'))
        .select_from(data)
        .group_by(data.c.name))

    result, = query.one()
    assert sorted(['foo']) == sorted(result.split(';'))


def test_group_concat_multi_value(db_session):
    """
    It should be able to delimit-multiple values
    """
    from sqlalchemy import literal_column, cast, Unicode
    from occams_datastore.utils.sql import group_concat

    data = (
        db_session.query(
            cast(literal_column("'myitem'"), Unicode).label('name'),
            cast(literal_column("'foo'"), Unicode).label('value'))
        .union(
            db_session.query(
                cast(literal_column("'myitem'"), Unicode).label('name'),
                cast(literal_column("'bar'"), Unicode).label('value')))
        .subquery())

    query = (
        db_session.query(group_concat(data.c.value, ';'))
        .select_from(data)
        .group_by(data.c.name))

    result, = query.one()
    assert sorted(['foo', 'bar']) == sorted(result.split(';'))


def test_group_concat_sqlite_one_arg(db_session):
    """
    It should use SQLite's deafult arguments (comma delimiter)
    """
    from sqlalchemy import literal_column
    from occams_datastore.utils.sql import group_concat

    if db_session.bind.url.drivername != 'sqlite':
        pytest.skip('Not using SQLite')

    data = (
        db_session.query(
            literal_column("'myitem'").label('name'),
            literal_column("'foo'").label('value'))
        .union(
            db_session.query(
                literal_column("'myitem'").label('name'),
                literal_column("'bar'").label('value')))
        .subquery())

    query = (
        db_session.query(group_concat(data.c.value))
        .select_from(data)
        .group_by(data.c.name))

    result, = query.one()
    assert sorted(['foo', 'bar']) == sorted(result.split(','))


def test_group_concat_sqlite_invalid_args(db_session):
    """
    It should only support at most two arguments in SQLite
    """
    from sqlalchemy import literal_column
    from occams_datastore.utils.sql import group_concat

    if db_session.bind.url.drivername != 'sqlite':
        pytest.skip('Not using SQLite')

    data = (
        db_session.query(
            literal_column("'myitem'").label('name'),
            literal_column("'foo'").label('value'))
        .union(
            db_session.query(
                literal_column("'myitem'").label('name'),
                literal_column("'bar'").label('value')))
        .subquery())

    query = (
        db_session.query(group_concat(data.c.value, ';', 'wtf'))
        .select_from(data)
        .group_by(data.c.name))

    with pytest.raises(TypeError):
        result, = query.one()


def test_group_concat_postgresql_invalid_args(db_session):
    """
    It should only support at least two arguments in PostgreSQL
    """
    from sqlalchemy import literal_column
    from occams_datastore.utils.sql import group_concat

    if db_session.bind.url.drivername != 'postgresql':
        pytest.skip('Not using PostgreSQL')

    data = (
        db_session.query(
            literal_column("'myitem'").label('name'),
            literal_column("'foo'").label('value'))
        .union(
            db_session.query(
                literal_column("'myitem'").label('name'),
                literal_column("'bar'").label('value')))
        .subquery())

    query = (
        db_session.query(group_concat(data.c.value))
        .select_from(data)
        .group_by(data.c.name))

    with pytest.raises(TypeError):
        result, = query.one()


def test_to_date(db_session):
    """
    It should be able to cast to a date
    """
    import datetime
    from sqlalchemy import literal_column
    from occams_datastore.utils.sql import to_date

    expected = datetime.date(1976, 7, 4)
    query = (
        db_session.query(
            to_date(literal_column("'%s'" % expected)).label('value')))

    result, = query.one()
    assert str(expected) == str(result)


def test_to_datetime(db_session):
    """
    It should be able to cast to a datetime
    """
    import datetime
    from sqlalchemy import literal_column
    from occams_datastore.utils.sql import to_datetime

    expected = datetime.datetime(1976, 7, 4, 5, 0)
    query = (
        db_session.query(
            to_datetime(literal_column("'%s'" % expected)).label('value')))

    result, = query.one()
    assert str(expected) == str(result)


def test_json(db_session):
    """
    It should be able to marshall JSON data
    """

    db_session.add(SomeMapping(value=None))
    record = db_session.query(SomeMapping).one()
    assert record.value is None

    some_json_value = record.value = {
        'foo': 'some val',
        'bar': 420}
    db_session.flush()

    # Clear all session objects so that they can be reloaded
    db_session.expunge_all()

    record = db_session.query(SomeMapping).one()
    assert sorted(some_json_value.values()) == \
        sorted(record.value.values())


def test_json_native_postgresql(db_session):
    """
    It should use PostgreSQL's native JSON implementation
    """
    if db_session.bind.url.drivername != 'postgresql':
        pytest.skip('Not using PostgreSQL')

    assert SomeMapping.value.type.compile(db_session.bind.dialect) == 'JSON'
