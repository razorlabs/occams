"""
Tests for storage implementations and services
"""

from nose.tools import with_setup

from tests import Session, begin_func, rollback_func


@with_setup(begin_func, rollback_func)
def test_state_unique_name():
    """
    It should only allow states with unique names
    """
    from nose.tools import assert_raises
    import sqlalchemy.exc
    from occams.datastore import models

    Session.add(models.State(name=u'pending-entry', title=u'Pending Entry'))
    Session.flush()

    Session.add(models.State(name=u'pending-entry', title=u'Pending Entry'))
    assert_raises(sqlalchemy.exc.IntegrityError, Session.flush)


@with_setup(begin_func, rollback_func)
def test_state_entity_relationship():
    """
    It should implement state/entity relationship
    """
    from datetime import date
    from nose.tools import assert_is_none, assert_is_not_none, assert_equals
    from occams.datastore import models

    schema = models.Schema(name=u'Foo', title=u'Foo',
                           publish_date=date(2000, 1, 1))
    pending_entry = models.State(name=u'pending-entry', title=u'Pending Entry')
    entity = models.Entity(schema=schema, name='foo', title=u'Foo')
    Session.add_all([pending_entry, entity])
    Session.flush()

    assert_is_none(entity.state)
    assert_equals(pending_entry.entities.count(), 0)

    entity.state = pending_entry
    Session.flush()

    assert_is_not_none(entity.state)
    assert_equals(pending_entry.entities.count(), 1)


@with_setup(begin_func, rollback_func)
def test_entity_add_unpublished_schema():
    """
    It should not allow adding entities related to unpublished schemata
    """
    from nose.tools import assert_raises
    from occams.datastore import models
    from occams.datastore.exc import InvalidEntitySchemaError

    schema = models.Schema(name=u'Foo', title=u'')
    entity = models.Entity(schema=schema, name=u'Foo', title=u'')
    Session.add(entity)
    with assert_raises(InvalidEntitySchemaError):
        Session.flush()


@with_setup(begin_func, rollback_func)
def test_entity_default_collect_date():
    """
    It should default to today's date as the collect_date if not is provided
    """
    from datetime import date
    from nose.tools import assert_equals
    from occams.datastore import models
    # Make sure the system can auto-assign a collect date for the entry

    schema = models.Schema(name=u'Foo', title=u'',
                           publish_date=date(2000, 1, 1))
    entity = models.Entity(schema=schema, name=u'Foo', title=u'')
    Session.add(entity)
    Session.flush()
    assert_equals(date.today(), entity.collect_date)

    # If one is supplied by the user, don't do anything
    collect_date = date(2010, 9, 1)
    entity = models.Entity(
        schema=schema,
        name=u'Entry 2',
        title=u'Entry 2',
        collect_date=collect_date)
    Session.add(entity)
    Session.flush()
    assert_equals(entity.collect_date, collect_date)


def test_entity_types():
    """
    It should properly handle supported types
    """

    from datetime import date, datetime
    from decimal import Decimal

    data = [
        ('integer', 5, 8, [1, 2, 3]),
        ('decimal',
            Decimal('16.4'),
            Decimal('12.3'),
            [Decimal('1.5'), Decimal('12.1'), Decimal('3.0')]),
        ('boolean', True, False, [True, False]),
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
             datetime(2010, 8, 1, 5, 3, 0)])]

    for args in data:
        yield (check_entity_types,) + args


@with_setup(begin_func, rollback_func)
def check_entity_types(type, simple, update, collection):
    """
    Assert method to stress-test a spcific type
    """
    from datetime import date
    from nose.tools import assert_is_none, assert_equals, assert_items_equal
    from occams.datastore import models

    schema = models.Schema(name=u'Foo', title=u'',
                           publish_date=date(2000, 1, 1))
    section = models.Section(
        schema=schema, name='section', title=u'Section 1', order=0)
    entity = models.Entity(schema=schema, name=u'Foo', title=u'')
    Session.add(entity)
    Session.flush()

    order = 0

    ModelClass = models.nameModelMap[type]

    # Do simple values
    simpleName = type + 'simple'

    schema.attributes[simpleName] = models.Attribute(
        name=simpleName,
        section=section,
        title=u'', type=type, is_required=False, order=order)
    assert_is_none(entity[simpleName])
    entity[simpleName] = None
    Session.flush()
    assert_is_none(entity[simpleName])

    entity[simpleName] = simple
    Session.flush()
    assert_equals(simple, entity[simpleName])

    # Double check auditing
    valueQuery = (
        Session.query(ModelClass)
        .filter_by(attribute=schema.attributes[simpleName]))
    valueObject = valueQuery.one()
    assert_equals(2, valueObject.revision)

    # Try updating
    entity[simpleName] = update
    Session.flush()
    assert_equals(update, entity[simpleName])

    # Triple check auditing
    valueObject = valueQuery.one()
    assert_equals(3, valueObject.revision)

    order += 1

    # Now try collections
    collectionName = type + 'collection'
    schema.attributes[collectionName] = models.Attribute(
        name=collectionName,
        schema=schema,
        section=section,
        title=u'', type=type, is_collection=True, order=order)
    entity[collectionName] = collection
    Session.flush()
    assert_equals(set(collection), set(entity[collectionName]))

    valueQuery = (
        Session.query(ModelClass)
        .filter_by(attribute=schema.attributes[collectionName]))

    order += 1

    # Make sure we can also update
    entity[collectionName] = collection[:2]
    Session.flush()
    assert_equals(set(collection[:2]), set(entity[collectionName]))
    assert_equals(2, valueQuery.count())

    # Lists are not audited, they're just removed and a new one is
    # set
    assert_items_equal([1, 1], [v.revision for v in valueQuery])


def test_entity_force_date():
    """
    It should maintain a date object for date types.
    (Sometimes applications will blindly assign datetimes...)
    """
    from datetime import date, datetime
    from nose.tools import assert_equals, assert_is_instance
    from occams.datastore import models

    schema = models.Schema(name=u'Foo', title=u'',
                           publish_date=date(2000, 1, 1))
    section = models.Section(
        schema=schema, name='section', title=u'Section 1', order=0)
    entity = models.Entity(schema=schema, name=u'Foo', title=u'')

    # Do simple values
    simpleName = 'choicesimple'
    schema.attributes[simpleName] = models.Attribute(
        schema=schema,
        section=section,
        title=u'', type='date', is_required=False, order=1)

    now = datetime.now()
    today = now.date()

    entity[simpleName] = now
    Session.flush()
    assert_is_instance(entity[simpleName], date)
    assert_equals(today, entity[simpleName])


@with_setup(begin_func, rollback_func)
def test_entity_choices():
    """
    It should properly handle choices
    """
    from datetime import date
    from nose.tools import assert_is_none, assert_equals, assert_items_equal
    from occams.datastore import models

    schema = models.Schema(name=u'Foo', title=u'',
                           publish_date=date(2000, 1, 1))
    section = models.Section(
        schema=schema, name='section', title=u'Section 1', order=0)
    entity = models.Entity(schema=schema, name=u'Foo', title=u'')
    Session.add(entity)
    Session.flush()

    # Do simple values
    simpleName = 'choicesimple'
    schema.attributes[simpleName] = models.Attribute(
        schema=schema,
        section=section,
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
    Session.flush()
    assert_is_none(entity[simpleName])

    entity[simpleName] = u'002'
    Session.flush()
    assert_equals(u'002', entity[simpleName])

    # Now try collections
    collectionName = 'choicecollection'
    schema.attributes[collectionName] = models.Attribute(
        schema=schema,
        section=section,
        name=collectionName,
        title=u'', type='choice', is_collection=True, order=2,
        choices={
            '001': models.Choice(name=u'001', title=u'Foo', order=1),
            '002': models.Choice(name=u'002', title=u'Bar', order=2),
            '003': models.Choice(name=u'003', title=u'Baz', order=3),
            '004': models.Choice(name=u'004', title=u'Caz', order=4),
            '005': models.Choice(name=u'005', title=u'Jaz', order=5)})
    entity[collectionName] = [u'001', u'002', u'005']
    Session.flush()
    assert_items_equal([u'001', u'002', u'005'], entity['choicecollection'])


@with_setup(begin_func, rollback_func)
def test_entity_blob_type():
    """
    It should support files storage
    """

    from occams.datastore import models
    from datetime import date
    import os
    from nose.tools import assert_equals

    schema = models.Schema(name='HasBlob', title=u'',
                           publish_date=date(2000, 1, 1))
    section = models.Section(
        schema=schema, name='section', title=u'Section 1', order=0)
    schema.attributes['theblob'] = models.Attribute(
        section=section, name=u'theblob', title=u'', type='blob', order=0)
    entity = models.Entity(schema=schema, name='blobish', title=u'')
    contents = os.urandom(1000)
    entity['theblob'] = contents
    Session.add(entity)
    Session.flush()
    entity_id = entity.id
    # remove all isntances from the Session so we can see if they are
    # properly fetched
    Session.expunge_all()

    entity = Session.query(models.Entity).get(entity_id)
    assert_equals(contents, entity['theblob'])
    assert_equals(1, Session.query(models.ValueBlob).count())


def test_value_min_constraint():
    """
    It should validate against minimum constratins
    """
    from datetime import date, datetime
    from decimal import Decimal
    import time

    data = [
        ('string', 5, u'foo', u'foooo', u'foobario'),
        ('integer', 5, 2, 5, 10),
        ('decimal', 5, Decimal('2.0'), Decimal('5.0'), Decimal('10.0')),
        ('date',
            time.mktime(date(2009, 5, 6).timetuple()),
            date(2001, 2, 8), date(2009, 5, 6),
            date(2010, 4, 6)),
        ('datetime',
            time.mktime(date(2009, 5, 6).timetuple()),
            datetime(2001, 2, 8),
            datetime(2009, 5, 6),
            datetime(2010, 4, 6))]

    for args in data:
        yield (check_value_min_constraint,) + args


@with_setup(begin_func, rollback_func)
def check_value_min_constraint(type_, limit, below, equal, over):
    """
    Assert method to stress-test minimum constraints
    """
    from datetime import date
    from nose.tools import assert_raises
    from occams.datastore import models
    from occams.datastore.exc import ConstraintError

    schema = models.Schema(
        name=u'Foo', title=u'', publish_date=date(2000, 1, 1))
    section = models.Section(
        schema=schema, name='section', title=u'Section 1', order=0)
    entity = models.Entity(schema=schema, name=u'Foo', title=u'')
    Session.add(entity)
    Session.flush()

    models.Attribute(
        schema=schema, section=section,
        name=type_, title=u'',
        type=type_, is_required=False, value_min=limit, order=0)

    with assert_raises(ConstraintError):
        entity[type_] = below

    entity[type_] = None
    entity[type_] = equal
    entity[type_] = over

    models.Attribute(
        schema=schema, section=section,
        name=u'boolean', title=u'', type=u'boolean', value_min=10, order=1)

    with assert_raises(NotImplementedError):
        entity['boolean'] = True


def test_value_max_constraint():
    """
    It should validate against maximum constraints
    """
    import time
    from datetime import date, datetime
    from decimal import Decimal

    data = [
        # (type, limit, below, equal, over)
        ('string', 5, u'foo', u'foooo', u'foobario'),
        ('integer', 5, 2, 5, 10),
        ('decimal', 5, Decimal('2.0'), Decimal('5.0'), Decimal('10.0')),
        ('date',
            time.mktime(date(2009, 5, 6).timetuple()),
            date(2001, 2, 8), date(2009, 5, 6),
            date(2010, 4, 6)),
        ('datetime',
            time.mktime(date(2009, 5, 6).timetuple()),
            datetime(2001, 2, 8),
            datetime(2009, 5, 6),
            datetime(2010, 4, 6))]

    for args in data:
        yield (check_value_max_constraint,) + args


@with_setup(begin_func, rollback_func)
def check_value_max_constraint(type_, limit, below, equal, over):
    """
    Assert method to stress-test max constraint values
    """
    from datetime import date
    from nose.tools import assert_raises
    from occams.datastore import models
    from occams.datastore.exc import ConstraintError

    schema = models.Schema(name=u'Foo', title=u'',
                           publish_date=date(2000, 1, 1))
    section = models.Section(
        schema=schema, name='section', title=u'Section 1', order=0)
    entity = models.Entity(schema=schema, name=u'Foo', title=u'')
    Session.add(entity)
    Session.flush()

    models.Attribute(
        schema=schema, section=section,
        name=type_, title=u'', type=type_, is_required=False,
        value_max=limit, order=0)

    entity[type_] = None
    entity[type_] = below
    entity[type_] = equal

    with assert_raises(ConstraintError):
        entity[type_] = over

    models.Attribute(
        schema=schema, section=section,
        name=u'boolean', title=u'', type=u'boolean', value_max=10, order=1)
    with assert_raises(NotImplementedError):
        entity['boolean'] = True


@with_setup(begin_func, rollback_func)
def test_validator_constraint():
    """
    It should validate against string pattern constraints
    """
    from datetime import date
    from nose.tools import assert_raises, assert_equals
    from occams.datastore import models
    from occams.datastore.exc import ConstraintError

    schema = models.Schema(name=u'Foo', title=u'',
                           publish_date=date(2000, 1, 1))
    section = models.Section(
        schema=schema, name='section', title=u'Section 1', order=0)
    models.Attribute(
        schema=schema,
        section=section,
        name=u'test',
        title=u'',
        type=u'string',
        is_required=False,
        # Valid US phone number
        validator=r'\d{3}-\d{3}-\d{4}',
        order=0)
    Session.add(schema)
    Session.flush()

    entity = models.Entity(schema=schema, name=u'Foo', title=u'')
    Session.add(entity)

    entity['test'] = None

    with assert_raises(ConstraintError):
        entity['test'] = u'trollol'

    entity['test'] = u'123-456-7890'
    Session.flush()
    assert_equals('123-456-7890', entity['test'])


@with_setup(begin_func, rollback_func)
def test_choice_constraint():
    """
    It should validate against choice constraints
    """
    from datetime import date
    from nose.tools import assert_raises, assert_equals
    from occams.datastore import models
    from occams.datastore.exc import ConstraintError

    schema = models.Schema(name=u'Foo', title=u'',
                           publish_date=date(2000, 1, 1))
    section = models.Section(
        schema=schema, name='section', title=u'Section 1', order=0)
    models.Attribute(
        schema=schema, section=section,
        name=u'test', title=u'', type=u'choice', is_required=False, order=0,
        choices={
            '001': models.Choice(name=u'001', title=u'Foo', order=0),
            '002': models.Choice(name=u'002', title=u'Bar', order=1),
            '003': models.Choice(name=u'003', title=u'Baz', order=2)})
    Session.add(schema)
    Session.flush()

    entity = models.Entity(schema=schema, name=u'FooEntry', title=u'')
    Session.add(entity)

    entity['test'] = None
    entity['test'] = u'002'
    Session.flush()

    entry = (
        Session.query(models.ValueChoice)
        .filter(models.ValueChoice.value.has(name=u'002'))
        .one())
    assert_equals(entry.value.name, '002')

    # Should not be able to set it to something outside of the specified
    # choice constraints

    with assert_raises(ConstraintError):
        entity['test'] = u'999'


def test_has_entities():
    """
    It should allow any table to be associated with entities (yuk!)
    """
    from datetime import date
    from nose.tools import (
        assert_is_not_none, assert_equals, assert_items_equal)
    from sqlalchemy import create_engine, Column, Integer, String
    from sqlalchemy.orm import scoped_session, sessionmaker
    from occams.datastore import models
    from occams.datastore.models.events import register

    Session = scoped_session(sessionmaker(
        bind=create_engine('sqlite://'),
        info={'user': 'foo@foo.com'}))
    register(Session)

    class SampleClass1(models.DataStoreModel, models.HasEntities):
        __tablename__ = 'sampleclass1'

        id = Column(Integer, primary_key=True)

        name = Column(String, nullable=False)

    class SampleClass2(models.DataStoreModel, models.HasEntities):
        __tablename__ = 'sampleclass2'

        id = Column(Integer, primary_key=True)

        name = Column(String, nullable=False)

    # Register a default user
    models.DataStoreModel.metadata.create_all(Session.bind)
    Session.add(models.User(key='foo@foo.com'))
    Session.flush()

    # Sample schemata
    schemaA = models.Schema(name=u'A', title=u'',
                            publish_date=date(2000, 1, 1))
    schemaB = models.Schema(name=u'B', title=u'',
                            publish_date=date(2000, 1, 1))

    Session.add_all([
        SampleClass1(
            name='Foo',
            entities=[
                models.Entity(schema=schemaA, name='foo', title=u''),
                models.Entity(schema=schemaA, name='bar', title=u''),
                models.Entity(schema=schemaB, name='baz', title=u'')]),
        SampleClass2(
            name='Bar',
            entities=[
                models.Entity(schema=schemaA, name='caz', title=u''),
                models.Entity(schema=schemaB, name='raz', title=u'')])])

    Session.flush()

    # Verify that the data was correctly associated
    sc1 = Session.query(SampleClass1).filter_by(name='Foo').one()
    assert_equals(3, len(sc1.entities))
    assert_items_equal(['foo', 'bar', 'baz'], [e.name for e in sc1.entities])

    # Add one more to verify collection_class is of type "set"
    sc1.entities.add(models.Entity(schema=schemaB, name='car', title=u''),)
    Session.flush()
    assert_items_equal(['foo', 'bar', 'baz', 'car'],
                       [e.name for e in sc1.entities])

    sc2 = Session.query(SampleClass2).filter_by(name='Bar').one()
    assert_equals(2, len(sc2.entities))
    assert_items_equal(['raz', 'caz'], [e.name for e in sc2.entities])

    # I want a SampleClass1 that contains specific schemata
    query = (
        Session.query(SampleClass1)
        .filter(SampleClass1.name == 'Foo')
        .filter(SampleClass1.entities.any(models.Schema.name == u'A')))

    sc1 = query.one()
    assert_is_not_none(sc1)

    # Now suppose that we only have an fooEntity and want to know its parents
    # Example: get all the SomeClassX references of an fooEntity

    fooEntity = Session.query(models.Entity).filter_by(name=u'foo').one()

    sc1list = [c.sampleclass1_parent.name
               for c in fooEntity.contexts if c.sampleclass1_parent]
    assert_items_equal(['Foo'], sc1list)

    # Querying them directly
    # There is no clean way of querying for an fooEntity by context in
    # a generic association setting, as it would have to know about
    # all ``HasEntities`` classes that reference it
    sc1EntitiesQuery = (
        Session.query(models.Entity)
        .join(models.Entity.contexts)
        .filter(models.Context.external == u'sampleclass1')
        .join(SampleClass1, (SampleClass1.id == models.Context.key))
        .filter(SampleClass1.name == 'Foo'))

    entitylist = [e.name for e in sc1EntitiesQuery]
    assert_items_equal(['foo', 'bar', 'car', 'baz'], entitylist)

    # Now try adding the fooEntity to an additional context
    Session.add(SampleClass1(name='Jar', entities=[fooEntity]))
    Session.flush()

    sc1list = [c.sampleclass1_parent.name
               for c in fooEntity.contexts if c.sampleclass1_parent]
    assert_items_equal(['Foo', 'Jar'], sc1list)

    # But what if you want to query them directly? Same as above, query
    # for a SampleClass that contains the specific schemata you want
    hasFooQuery = (
        Session.query(SampleClass1)
        .filter(SampleClass1.entities.any(models.Entity.name == u'foo')))

    sc1list = [i.name for i in hasFooQuery]
    assert_items_equal(['Foo', 'Jar'], sc1list)

    # Now try deleting a context object
    sc1 = Session.query(SampleClass1).filter_by(name=u'Foo').one()
    Session.delete(sc1)
    Session.flush()

    assert_equals(0, sc1EntitiesQuery.count())

    # Make sure we didn't accidentally remote the data from 'Jar'
    sc1list = [i.name for i in hasFooQuery]
    assert_items_equal(['Jar'], sc1list)

    # Double check just in case
    count = (
        Session.query(models.Context)
        .filter_by(external='sampleclass1')
        .count())
    assert_equals(count, 1)

    count = (
        Session.query(models.Entity)
        .filter_by(name=u'foo')
        .count())
    assert_equals(1, count)

    # TODO Currently there is absolutely no way to remove orphans. The
    # application must do this manually. This is because assocation proxies
    # cannot delete orphans and the way the relationships are setup, it
    # does not allow this..
