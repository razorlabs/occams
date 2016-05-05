"""
Tests for storage implementations and services
"""

import time
from datetime import date, datetime
from decimal import Decimal

import pytest


def test_state_unique_name(db_session):
    """
    It should only allow states with unique names
    """
    import sqlalchemy.exc
    from occams_datastore import models

    db_session.add(models.State(name=u'pending-entry', title=u'Pending Entry'))
    db_session.flush()

    db_session.add(models.State(name=u'pending-entry', title=u'Pending Entry'))
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        db_session.flush()


def test_state_entity_relationship(db_session):
    """
    It should implement state/entity relationship
    """
    from datetime import date
    from occams_datastore import models

    schema = models.Schema(name=u'Foo', title=u'Foo',
                           publish_date=date(2000, 1, 1))
    pending_entry = models.State(name=u'pending-entry', title=u'Pending Entry')
    entity = models.Entity(schema=schema)
    db_session.add_all([pending_entry, entity])
    db_session.flush()

    assert entity.state is None
    assert pending_entry.entities.count() == 0

    entity.state = pending_entry
    db_session.flush()

    assert entity.state is not None
    assert pending_entry.entities.count() == 1


def test_entity_add_unpublished_schema(db_session):
    """
    It should not allow adding entities related to unpublished schemata
    """
    from occams_datastore import models
    from occams_datastore.exc import InvalidEntitySchemaError

    schema = models.Schema(name=u'Foo', title=u'')
    entity = models.Entity(schema=schema)
    db_session.add(entity)
    with pytest.raises(InvalidEntitySchemaError):
        db_session.flush()


def test_entity_default_collect_date(db_session):
    """
    It should default to today's date as the collect_date if not is provided
    """
    from datetime import date
    from occams_datastore import models
    # Make sure the system can auto-assign a collect date for the entry

    schema = models.Schema(name=u'Foo', title=u'',
                           publish_date=date(2000, 1, 1))
    entity = models.Entity(schema=schema)
    db_session.add(entity)
    db_session.flush()
    assert date.today() == entity.collect_date

    # If one is supplied by the user, don't do anything
    collect_date = date(2010, 9, 1)
    entity = models.Entity(
        schema=schema,
        collect_date=collect_date)
    db_session.add(entity)
    db_session.flush()
    assert entity.collect_date == collect_date


@pytest.mark.parametrize('type,simple,update,collection', [
    ('number',
        Decimal('16.4'),
        Decimal('12.3'),
        [Decimal('1.5'), Decimal('12.1'), Decimal('3.0')]),
    ('string', u'foo', u'bar', [u'foo', u'bar', u'baz']),
    ('text', u'foo\nbar', u'foo\nbario',
        [u'par\n1', u'par\n2', u'par\n3']),
    ('date', date(2010, 3, 1), date(2010, 4, 1),
        [date(2010, 1, 1), date(2010, 2, 1), date(2010, 3, 1)]),
    ('datetime',
        datetime(2010, 3, 1, 5, 3, 0),
        datetime(2011, 3, 1, 5, 3, 0),
        [datetime(2010, 3, 1, 5, 3, 0),
         datetime(2010, 5, 1, 5, 3, 0),
         datetime(2010, 8, 1, 5, 3, 0)])
])
def check_entity_types(db_session, type, simple, update, collection):
    """
    It should properly handle supported types
    """
    from datetime import date
    from occams_datastore import models

    schema = models.Schema(
        name=u'Foo', title=u'',
        publish_date=date(2000, 1, 1),
        attributes={
            's1': models.Attribute(
                name='s1', title=u'Section 1', type='section', order=1)})
    entity = models.Entity(schema=schema)
    db_session.add(entity)
    db_session.flush()

    order = 1

    ModelClass = models.nameModelMap[type]

    # Do simple values
    simpleName = type + 'simple'

    # Try null first
    schema.attributes['s1'].attributes[simpleName] = models.Attribute(
        name=simpleName,
        title=u'', type=type, is_required=False, order=order)
    assert entity[simpleName] is None
    entity[simpleName] = None
    db_session.flush()
    assert entity[simpleName] is None

    # Update value
    entity[simpleName] = simple
    db_session.flush()
    assert simple == entity[simpleName]

    # Double check auditing
    valueQuery = (
        db_session.query(ModelClass)
        .filter_by(attribute=schema.attributes[simpleName]))
    valueObject = valueQuery.one()
    assert 1 == valueObject.revision

    # Update again
    entity[simpleName] = update
    db_session.flush()
    assert update == entity[simpleName]

    # Triple check auditing
    valueObject = valueQuery.one()
    assert 2 == valueObject.revision

    order += 1

    # Now try collections
    collectionName = type + 'collection'
    schema.attributes['s1'].attributes[collectionName] = models.Attribute(
        name=collectionName,
        schema=schema,
        title=u'', type=type, is_collection=True, order=order)
    entity[collectionName] = collection
    db_session.flush()
    assert set(collection) == set(entity[collectionName])

    valueQuery = (
        db_session.query(ModelClass)
        .filter_by(attribute=schema.attributes[collectionName]))

    order += 1

    # Make sure we can also update
    entity[collectionName] = collection[:2]
    db_session.flush()
    assert set(collection[:2]) == set(entity[collectionName])
    assert 2 == valueQuery.count()

    # Lists are not audited, they're just removed and a new one is
    # set
    assert sorted([1, 1]) == sorted([v.revision for v in valueQuery])


def test_entity_force_date(db_session):
    """
    It should maintain a date object for date types.
    (Sometimes applications will blindly assign datetimes...)
    """
    from datetime import date, datetime
    from occams_datastore import models

    schema = models.Schema(name=u'Foo', title=u'',
                           publish_date=date(2000, 1, 1))
    s1 = models.Attribute(
        schema=schema, name='s1', title=u'Section 1', type='section', order=0)
    entity = models.Entity(schema=schema)

    # Do simple values
    simpleName = 'choicesimple'
    schema.attributes[simpleName] = models.Attribute(
        schema=schema,
        parent_attribute=s1,
        title=u'', type='date', is_required=False, order=1)

    now = datetime.now()
    today = now.date()

    entity[simpleName] = now
    db_session.flush()
    assert isinstance(entity[simpleName], date)
    assert today == entity[simpleName]


def test_entity_choices(db_session):
    """
    It should properly handle choices
    """
    from datetime import date
    from occams_datastore import models

    schema = models.Schema(name=u'Foo', title=u'',
                           publish_date=date(2000, 1, 1))
    s1 = models.Attribute(
        schema=schema, name='s1', title=u'Section 1', type='section', order=0)
    entity = models.Entity(schema=schema)
    db_session.add(entity)
    db_session.flush()

    # Do simple values
    simpleName = 'choicesimple'
    schema.attributes[simpleName] = models.Attribute(
        schema=schema,
        parent_attribute=s1,
        name=simpleName,
        title=u'', type='choice', is_required=False, order=1,
        choices={
            '001': models.Choice(name=u'001', title=u'Foo', order=1),
            '002': models.Choice(name=u'002', title=u'Bar', order=2),
            '003': models.Choice(name=u'003', title=u'Baz', order=3),
            '004': models.Choice(name=u'004', title=u'Caz', order=4),
            '005': models.Choice(name=u'005', title=u'Jaz', order=5),
            })
    entity[simpleName] = None
    db_session.flush()
    assert entity[simpleName] is None

    entity[simpleName] = u'002'
    db_session.flush()
    assert u'002' == entity[simpleName]

    # Now try collections
    collectionName = 'choicecollection'
    schema.attributes[collectionName] = models.Attribute(
        schema=schema,
        parent_attribute=s1,
        name=collectionName,
        title=u'', type='choice', is_collection=True, order=2,
        choices={
            '001': models.Choice(name=u'001', title=u'Foo', order=1),
            '002': models.Choice(name=u'002', title=u'Bar', order=2),
            '003': models.Choice(name=u'003', title=u'Baz', order=3),
            '004': models.Choice(name=u'004', title=u'Caz', order=4),
            '005': models.Choice(name=u'005', title=u'Jaz', order=5)})
    entity[collectionName] = [u'001', u'002', u'005']
    db_session.flush()
    assert sorted([u'001', u'002', u'005']) == \
        sorted(entity['choicecollection'])


def test_entity_blob_type(db_session):
    """
    It should be able to keep track of file uploads (will not be storing in DB)
    """

    from occams_datastore import models
    from datetime import date

    schema = models.Schema(name='HasBlob', title=u'',
                           publish_date=date(2000, 1, 1))
    s1 = models.Attribute(
        schema=schema, name='s1', title=u'Section 1', type='section', order=0)
    schema.attributes['theblob'] = models.Attribute(
        parent_attribute=s1,
        name=u'theblob', title=u'', type='blob', order=0)

    entity = models.Entity(schema=schema)
    db_session.add(entity)
    db_session.flush()
    entity_id = entity.id

    # Add value
    entity['theblob'] = models.BlobInfo(file_name=u'foo', path='bar/baz.gif')
    db_session.add(entity)
    db_session.flush()
    entity = db_session.query(models.Entity).get(entity_id)
    blob = entity['theblob']
    assert u'foo' == blob.file_name
    assert 'bar/baz.gif' == blob.path

    # Clear value
    entity['theblob'] = None
    db_session.flush()
    entity = db_session.query(models.Entity).get(entity_id)
    blob = entity['theblob']
    assert blob is None


@pytest.mark.parametrize('type_,limit,below,equal,over', [
    ('string', 5, u'foo', u'foooo', u'foobario'),
    ('number', 5, Decimal('2.0'), Decimal('5.0'), Decimal('10.0')),
    ('date',
        time.mktime(date(2009, 5, 6).timetuple()),
        date(2001, 2, 8), date(2009, 5, 6),
        date(2010, 4, 6)),
    ('datetime',
        time.mktime(date(2009, 5, 6).timetuple()),
        datetime(2001, 2, 8),
        datetime(2009, 5, 6),
        datetime(2010, 4, 6))
])
def check_value_min_constraint(db_session, type_, limit, below, equal, over):
    """
    It should validate against minimum constratins
    """
    from datetime import date
    from occams_datastore import models
    from occams_datastore.exc import ConstraintError

    schema = models.Schema(
        name=u'Foo', title=u'', publish_date=date(2000, 1, 1))
    s1 = models.Attribute(
        schema=schema, name='s1', title=u'Section 1', type='section', order=0)
    entity = models.Entity(schema=schema)
    db_session.add(entity)
    db_session.flush()

    models.Attribute(
        schema=schema, parent_attribute=s1,
        name=type_, title=u'',
        type=type_, is_required=False, value_min=limit, order=0)

    with pytest.raises(ConstraintError):
        entity[type_] = below

    entity[type_] = None
    entity[type_] = equal
    entity[type_] = over

    models.Attribute(
        schema=schema, parent_attribute=s1,
        name=u'boolean', title=u'', type=u'boolean', value_min=10, order=1)

    with pytest.raises(NotImplementedError):
        entity['boolean'] = True


@pytest.mark.parametrize('type_,limit,below,equal,over', [
    # (type, limit, below, equal, over)
    ('string', 5, u'foo', u'foooo', u'foobario'),
    ('number', 5, Decimal('2.0'), Decimal('5.0'), Decimal('10.0')),
    ('date',
        time.mktime(date(2009, 5, 6).timetuple()),
        date(2001, 2, 8), date(2009, 5, 6),
        date(2010, 4, 6)),
    ('datetime',
        time.mktime(date(2009, 5, 6).timetuple()),
        datetime(2001, 2, 8),
        datetime(2009, 5, 6),
        datetime(2010, 4, 6))
])
def check_value_max_constraint(db_session, type_, limit, below, equal, over):
    """
    It should validate against maximum constraints
    """
    from datetime import date
    from occams_datastore import models
    from occams_datastore.exc import ConstraintError

    schema = models.Schema(name=u'Foo', title=u'',
                           publish_date=date(2000, 1, 1))
    s1 = models.Attribute(
        schema=schema, name='s1', title=u'Section 1', type='section', order=0)
    entity = models.Entity(schema=schema)
    db_session.add(entity)
    db_session.flush()

    models.Attribute(
        schema=schema, parent_attribute=s1,
        name=type_, title=u'', type=type_, is_required=False,
        value_max=limit, order=0)

    entity[type_] = None
    entity[type_] = below
    entity[type_] = equal

    with pytest.raises(ConstraintError):
        entity[type_] = over

    models.Attribute(
        schema=schema, parent_attribute=s1,
        name=u'boolean', title=u'', type=u'boolean', value_max=10, order=1)
    with pytest.raises(NotImplementedError):
        entity['boolean'] = True


def test_validator_min_constraint(db_session):
    """
    It should validate string/number value min/max
    """
    from datetime import date
    from occams_datastore import models
    from occams_datastore.exc import ConstraintError

    schema = models.Schema(name=u'Foo', title=u'',
                           publish_date=date(2000, 1, 1))
    s1 = models.Attribute(
        schema=schema, name='s1', title=u'Section 1', type='section', order=0)
    models.Attribute(
        schema=schema,
        parent_attribute=s1,
        name=u'test',
        title=u'',
        type=u'string',
        is_required=False,
        value_min=3,
        order=0)
    db_session.add(schema)
    db_session.flush()

    entity = models.Entity(schema=schema)
    db_session.add(entity)

    entity['test'] = None

    with pytest.raises(ConstraintError):
        entity['test'] = u'f'

    entity['test'] = u'foo'
    db_session.flush()
    assert 'foo' == entity['test']


def test_validator_max_constraint(db_session):
    """
    It should validate string/number value min/max
    """
    from datetime import date
    from occams_datastore import models
    from occams_datastore.exc import ConstraintError

    schema = models.Schema(name=u'Foo', title=u'',
                           publish_date=date(2000, 1, 1))
    s1 = models.Attribute(
        schema=schema, name='s1', title=u'Section 1', type='section', order=0)
    models.Attribute(
        schema=schema,
        parent_attribute=s1,
        name=u'test',
        title=u'',
        type=u'string',
        is_required=False,
        value_max=3,
        order=0)
    db_session.add(schema)
    db_session.flush()

    entity = models.Entity(schema=schema)
    db_session.add(entity)

    entity['test'] = None

    with pytest.raises(ConstraintError):
        entity['test'] = u'foobar'

    entity['test'] = u'foo'
    db_session.flush()
    assert 'foo' == entity['test']


def test_validator_pattern_constraint(db_session):
    """
    It should validate against string pattern constraints
    """
    from datetime import date
    from occams_datastore import models
    from occams_datastore.exc import ConstraintError

    schema = models.Schema(name=u'Foo', title=u'',
                           publish_date=date(2000, 1, 1))
    s1 = models.Attribute(
        schema=schema, name='s1', title=u'Section 1', type='section', order=0)
    models.Attribute(
        schema=schema,
        parent_attribute=s1,
        name=u'test',
        title=u'',
        type=u'string',
        is_required=False,
        # Valid US phone number
        pattern=r'\d{3}-\d{3}-\d{4}',
        order=0)
    db_session.add(schema)
    db_session.flush()

    entity = models.Entity(schema=schema)
    db_session.add(entity)

    entity['test'] = None

    with pytest.raises(ConstraintError):
        entity['test'] = u'trollol'

    entity['test'] = u'123-456-7890'
    db_session.flush()
    assert '123-456-7890' == entity['test']


def test_choice_constraint(db_session):
    """
    It should validate against choice constraints
    """
    from datetime import date
    from occams_datastore import models
    from occams_datastore.exc import ConstraintError

    schema = models.Schema(name=u'Foo', title=u'',
                           publish_date=date(2000, 1, 1))
    s1 = models.Attribute(
        schema=schema, name='s1', title=u'Section 1', type='section', order=0)
    models.Attribute(
        schema=schema, parent_attribute=s1,
        name=u'test', title=u'', type=u'choice', is_required=False, order=0,
        choices={
            '001': models.Choice(name=u'001', title=u'Foo', order=0),
            '002': models.Choice(name=u'002', title=u'Bar', order=1),
            '003': models.Choice(name=u'003', title=u'Baz', order=2)})
    db_session.add(schema)
    db_session.flush()

    entity = models.Entity(schema=schema)
    db_session.add(entity)

    entity['test'] = None
    entity['test'] = u'002'
    db_session.flush()

    entry = (
        db_session.query(models.ValueChoice)
        .filter(models.ValueChoice.value.has(name=u'002'))
        .one())
    assert entry.value.name == '002'

    # Should not be able to set it to something outside of the specified
    # choice constraints

    with pytest.raises(ConstraintError):
        entity['test'] = u'999'
