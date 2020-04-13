"""
Tests for storage implementations and services
"""

import time
from datetime import date, datetime
from decimal import Decimal

import pytest


def test_state_unique_name(dbsession):
    """
    It should only allow states with unique names
    """
    import sqlalchemy.exc
    from occams import models

    dbsession.add(models.State(name='a-unique-name', title='A unique name'))
    dbsession.flush()

    dbsession.add(models.State(name='a-unique-name', title='A unique name'))
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        dbsession.flush()


def test_state_entity_relationship(dbsession):
    """
    It should implement state/entity relationship
    """
    from datetime import date
    from occams import models

    schema = models.Schema(name='Foo', title='Foo',
                           publish_date=date(2000, 1, 1))
    pending_entry = \
        dbsession.query(models.State).filter_by(name='pending-entry').one()
    entity = models.Entity(schema=schema)
    dbsession.add_all([pending_entry, entity])
    dbsession.flush()

    assert entity.state is None
    assert pending_entry.entities.count() == 0

    entity.state = pending_entry
    dbsession.flush()

    assert entity.state is not None
    assert pending_entry.entities.count() == 1


def test_entity_default_collect_date(dbsession):
    """
    It should default to today's date as the collect_date if not is provided
    """
    from datetime import date
    from occams import models
    # Make sure the system can auto-assign a collect date for the entry

    schema = models.Schema(name='Foo', title='',
                           publish_date=date(2000, 1, 1))
    entity = models.Entity(schema=schema)
    dbsession.add(entity)
    dbsession.flush()
    assert date.today() == entity.collect_date

    # If one is supplied by the user, don't do anything
    collect_date = date(2010, 9, 1)
    entity = models.Entity(
        schema=schema,
        collect_date=collect_date)
    dbsession.add(entity)
    dbsession.flush()
    assert entity.collect_date == collect_date


@pytest.mark.parametrize('type,simple,update,collection', [
    ('number',
        Decimal('16.4'),
        Decimal('12.3'),
        [Decimal('1.5'), Decimal('12.1'), Decimal('3.0')]),
    ('string', 'foo', 'bar', ['foo', 'bar', 'baz']),
    ('text', 'foo\nbar', 'foo\nbario',
        ['par\n1', 'par\n2', 'par\n3']),
    ('date', date(2010, 3, 1), date(2010, 4, 1),
        [date(2010, 1, 1), date(2010, 2, 1), date(2010, 3, 1)]),
    ('datetime',
        datetime(2010, 3, 1, 5, 3, 0),
        datetime(2011, 3, 1, 5, 3, 0),
        [datetime(2010, 3, 1, 5, 3, 0),
         datetime(2010, 5, 1, 5, 3, 0),
         datetime(2010, 8, 1, 5, 3, 0)])
])
def check_entity_types(dbsession, type, simple, update, collection):
    """
    It should properly handle supported types
    """
    from datetime import date
    from occams import models

    schema = models.Schema(
        name='Foo', title='',
        publish_date=date(2000, 1, 1),
        attributes={
            's1': models.Attribute(
                name='s1', title='Section 1', type='section', order=1)})
    entity = models.Entity(schema=schema)
    dbsession.add(entity)
    dbsession.flush()

    order = 1

    ModelClass = models.nameModelMap[type]

    # Do simple values
    simpleName = type + 'simple'

    # Try null first
    schema.attributes['s1'].attributes[simpleName] = models.Attribute(
        name=simpleName,
        title='', type=type, is_required=False, order=order)
    assert entity[simpleName] is None
    entity[simpleName] = None
    dbsession.flush()
    assert entity[simpleName] is None

    # Update value
    entity[simpleName] = simple
    dbsession.flush()
    assert simple == entity[simpleName]

    # Double check auditing
    valueQuery = (
        dbsession.query(ModelClass)
        .filter_by(attribute=schema.attributes[simpleName]))
    valueObject = valueQuery.one()
    assert 1 == valueObject.revision

    # Update again
    entity[simpleName] = update
    dbsession.flush()
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
        title='', type=type, is_collection=True, order=order)
    entity[collectionName] = collection
    dbsession.flush()
    assert set(collection) == set(entity[collectionName])

    valueQuery = (
        dbsession.query(ModelClass)
        .filter_by(attribute=schema.attributes[collectionName]))

    order += 1

    # Make sure we can also update
    entity[collectionName] = collection[:2]
    dbsession.flush()
    assert set(collection[:2]) == set(entity[collectionName])
    assert 2 == valueQuery.count()

    # Lists are not audited, they're just removed and a new one is
    # set
    assert sorted([1, 1]) == sorted([v.revision for v in valueQuery])


def test_entity_choices(dbsession):
    """
    It should properly handle choices
    """
    from datetime import date
    from occams import models

    schema = models.Schema(name='Foo', title='',
                           publish_date=date(2000, 1, 1))
    s1 = models.Attribute(
        schema=schema, name='s1', title='Section 1', type='section', order=0)
    entity = models.Entity(schema=schema)
    dbsession.add(entity)
    dbsession.flush()
    dbsession.refresh(schema)

    # Do simple values
    simpleName = 'choicesimple'
    schema.attributes[simpleName] = models.Attribute(
        schema=schema,
        parent_attribute=s1,
        name=simpleName,
        title='', type='choice', is_required=False, order=1,
        choices={
            '001': models.Choice(name='001', title='Foo', order=1),
            '002': models.Choice(name='002', title='Bar', order=2),
            '003': models.Choice(name='003', title='Baz', order=3),
            '004': models.Choice(name='004', title='Caz', order=4),
            '005': models.Choice(name='005', title='Jaz', order=5),
            })
    dbsession.flush()
    dbsession.refresh(schema)
    entity[simpleName] = None
    dbsession.flush()
    assert entity[simpleName] is None

    entity[simpleName] = '002'
    dbsession.flush()
    assert '002' == entity[simpleName]

    # Now try collections
    collectionName = 'choicecollection'
    schema.attributes[collectionName] = models.Attribute(
        schema=schema,
        parent_attribute=s1,
        name=collectionName,
        title='', type='choice', is_collection=True, order=2,
        choices={
            '001': models.Choice(name='001', title='Foo', order=1),
            '002': models.Choice(name='002', title='Bar', order=2),
            '003': models.Choice(name='003', title='Baz', order=3),
            '004': models.Choice(name='004', title='Caz', order=4),
            '005': models.Choice(name='005', title='Jaz', order=5)})
    dbsession.flush()
    dbsession.refresh(schema)
    entity[collectionName] = ['001', '002', '005']
    dbsession.flush()
    assert sorted(['001', '002', '005']) == \
        sorted(entity['choicecollection'])


@pytest.mark.parametrize('type_,limit,below,equal,over', [
    ('string', 5, 'foo', 'foooo', 'foobario'),
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
def check_value_min_constraint(dbsession, type_, limit, below, equal, over):
    """
    It should validate against minimum constratins
    """
    from datetime import date
    from occams import models
    from occams.exc import ConstraintError

    schema = models.Schema(
        name='Foo', title='', publish_date=date(2000, 1, 1))
    s1 = models.Attribute(
        schema=schema, name='s1', title='Section 1', type='section', order=0)
    entity = models.Entity(schema=schema)
    dbsession.add(entity)
    dbsession.flush()

    models.Attribute(
        schema=schema, parent_attribute=s1,
        name=type_, title='',
        type=type_, is_required=False, value_min=limit, order=0)

    with pytest.raises(ConstraintError):
        entity[type_] = below

    entity[type_] = None
    entity[type_] = equal
    entity[type_] = over

    models.Attribute(
        schema=schema, parent_attribute=s1,
        name='boolean', title='', type='boolean', value_min=10, order=1)

    with pytest.raises(NotImplementedError):
        entity['boolean'] = True


@pytest.mark.parametrize('type_,limit,below,equal,over', [
    # (type, limit, below, equal, over)
    ('string', 5, 'foo', 'foooo', 'foobario'),
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
def check_value_max_constraint(dbsession, type_, limit, below, equal, over):
    """
    It should validate against maximum constraints
    """
    from datetime import date
    from occams import models
    from occams.exc import ConstraintError

    schema = models.Schema(name='Foo', title='',
                           publish_date=date(2000, 1, 1))
    s1 = models.Attribute(
        schema=schema, name='s1', title='Section 1', type='section', order=0)
    entity = models.Entity(schema=schema)
    dbsession.add(entity)
    dbsession.flush()

    models.Attribute(
        schema=schema, parent_attribute=s1,
        name=type_, title='', type=type_, is_required=False,
        value_max=limit, order=0)

    entity[type_] = None
    entity[type_] = below
    entity[type_] = equal

    with pytest.raises(ConstraintError):
        entity[type_] = over

    models.Attribute(
        schema=schema, parent_attribute=s1,
        name='boolean', title='', type='boolean', value_max=10, order=1)
    with pytest.raises(NotImplementedError):
        entity['boolean'] = True


def test_validator_min_constraint(dbsession):
    """
    It should validate string/number value min/max
    """
    from datetime import date
    from occams import models
    from occams.exc import ConstraintError

    schema = models.Schema(name='Foo', title='',
                           publish_date=date(2000, 1, 1))
    s1 = models.Attribute(
        schema=schema, name='s1', title='Section 1', type='section', order=0)
    models.Attribute(
        schema=schema,
        parent_attribute=s1,
        name='test',
        title='',
        type='string',
        is_required=False,
        value_min=3,
        order=0)
    dbsession.add(schema)
    dbsession.flush()
    dbsession.refresh(schema)

    entity = models.Entity(schema=schema)
    dbsession.add(entity)

    entity['test'] = None

    with pytest.raises(ConstraintError):
        entity['test'] = 'f'

    entity['test'] = 'foo'
    dbsession.flush()
    assert 'foo' == entity['test']


def test_validator_max_constraint(dbsession):
    """
    It should validate string/number value min/max
    """
    from datetime import date
    from occams import models
    from occams.exc import ConstraintError

    schema = models.Schema(name='Foo', title='',
                           publish_date=date(2000, 1, 1))
    s1 = models.Attribute(
        schema=schema, name='s1', title='Section 1', type='section', order=0)
    models.Attribute(
        schema=schema,
        parent_attribute=s1,
        name='test',
        title='',
        type='string',
        is_required=False,
        value_max=3,
        order=0)
    dbsession.add(schema)
    dbsession.flush()
    dbsession.refresh(schema)

    entity = models.Entity(schema=schema)
    dbsession.add(entity)

    entity['test'] = None

    with pytest.raises(ConstraintError):
        entity['test'] = 'foobar'

    entity['test'] = 'foo'
    dbsession.flush()
    assert 'foo' == entity['test']


def test_validator_pattern_constraint(dbsession):
    """
    It should validate against string pattern constraints
    """
    from datetime import date
    from occams import models
    from occams.exc import ConstraintError

    schema = models.Schema(name='Foo', title='',
                           publish_date=date(2000, 1, 1))
    s1 = models.Attribute(
        schema=schema, name='s1', title='Section 1', type='section', order=0)
    models.Attribute(
        schema=schema,
        parent_attribute=s1,
        name='test',
        title='',
        type='string',
        is_required=False,
        # Valid US phone number
        pattern=r'\d{3}-\d{3}-\d{4}',
        order=0)
    dbsession.add(schema)
    dbsession.flush()
    dbsession.refresh(schema)

    entity = models.Entity(schema=schema)
    dbsession.add(entity)

    entity['test'] = None

    with pytest.raises(ConstraintError):
        entity['test'] = 'trollol'

    entity['test'] = '123-456-7890'
    dbsession.flush()
    assert '123-456-7890' == entity['test']


def test_choice_constraint(dbsession):
    """
    It should validate against choice constraints
    """
    from datetime import date
    from occams import models
    from occams.exc import ConstraintError

    schema = models.Schema(name='Foo', title='',
                           publish_date=date(2000, 1, 1))
    s1 = models.Attribute(
        schema=schema, name='s1', title='Section 1', type='section', order=0)
    models.Attribute(
        schema=schema, parent_attribute=s1,
        name='test', title='', type='choice', is_required=False, order=0,
        choices={
            '001': models.Choice(name='001', title='Foo', order=0),
            '002': models.Choice(name='002', title='Bar', order=1),
            '003': models.Choice(name='003', title='Baz', order=2)})
    dbsession.add(schema)
    dbsession.flush()
    dbsession.refresh(schema)

    entity = models.Entity(schema=schema)
    dbsession.add(entity)
    dbsession.flush()

    entity['test'] = None
    entity['test'] = '002'
    dbsession.flush()

    assert entity.data['test'] == '002'

    # Should not be able to set it to something outside of the specified
    # choice constraints

    with pytest.raises(ConstraintError):
        entity['test'] = '999'
