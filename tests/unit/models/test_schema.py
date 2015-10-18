"""
Test case for schema implementations and services
"""

import pytest


def test_schema_attribute(db_session):
    """
    It should implement full schema/attribute/subattribute hierarchies
    """
    from datetime import date
    from occams_datastore import models
    schema = models.Schema(
        name=u'aform',
        title=u'A Form',
        publish_date=date.today(),
        attributes={
            'section1': models.Attribute(
                name=u'section1',
                title=u'Section 1',
                type='section',
                order=0,
                attributes={
                    'foo': models.Attribute(
                        name=u'foo',
                        title=u'Foo',
                        type=u'choice',
                        order=0,
                        choices={
                            '001': models.Choice(
                                name=u'001',
                                title=u'Green',
                                order=0)
                        })
                })
            })

    db_session.add(schema)
    db_session.flush()
    assert 'section1' in schema.attributes
    # Works both ways
    assert 'foo' in schema.attributes
    assert 'foo' in schema.attributes['section1'].attributes


def test_schema_defaults(db_session):
    """
    It should set schema defaults
    """
    from occams_datastore import models

    db_session.add(models.Schema(name=u'sample', title=u'Sample'))
    db_session.flush()

    schema = db_session.query(models.Schema).one()
    assert schema.description is None
    assert schema.storage == 'eav'
    assert schema.is_association is None
    assert schema.create_date is not None
    assert schema.create_user is not None
    assert schema.modify_date is not None
    assert schema.modify_user is not None


def test_schema_invalid_regexp_name(db_session):
    """
    It should prevent invalid names (See RE_VALID_NAME)
    """
    from datetime import date
    from occams_datastore import models
    with pytest.raises(ValueError):
        db_session.add(models.Schema(
            name='555SomeForm',
            title=u'Foo',
            publish_date=date(2014, 3, 31)))
        db_session.flush()


def test_schema_unique_case_insensitive(db_session):
    """
    It should enforce case-insensitive schemata
    """
    from datetime import date
    import sqlalchemy.exc
    from occams_datastore import models

    db_session.add(models.Schema(
        name='Foo',
        title=u'Foo',
        publish_date=date(2014, 3, 31)))
    db_session.flush()

    db_session.add(models.Schema(
        name='foo',
        title=u'Foo',
        publish_date=date(2014, 3, 31)))

    with pytest.raises(sqlalchemy.exc.IntegrityError):
        db_session.flush()


def test_schema_publish_date_unique(db_session):
    """
    It should enforce unique publish dates
    """

    from datetime import date
    import sqlalchemy.exc
    from occams_datastore import models

    # First version
    db_session.add(models.Schema(
        name='Foo',
        title=u'Foo',
        publish_date=date(2014, 3, 31)))
    db_session.flush()

    # Draft version
    db_session.add(models.Schema(
        name='Foo',
        title=u'Foo',
        publish_date=None))
    db_session.flush()

    # Add another published schema (not on the same date)
    # Publish, not on the same date
    db_session.add(models.Schema(
        name='Foo',
        title=u'Foo',
        publish_date=date(2014, 4, 1)))
    db_session.flush()

    # New version, same date (wrong)
    db_session.add(models.Schema(
        name='Foo',
        title=u'Foo',
        publish_date=date(2014, 4, 1)))

    with pytest.raises(sqlalchemy.exc.IntegrityError):
        db_session.flush()


def test_schema_has_private(db_session):
    """
    It should be able to determine if a schema has private attributes
    """
    from datetime import date
    from occams_datastore import models
    schema = models.Schema(
        name='Foo',
        title=u'Foo',
        publish_date=date(2014, 3, 31),
        attributes={
            'not_private': models.Attribute(
                name='not_private',
                title=u'',
                type='string',
                is_private=False,
                order=0)
        })
    db_session.add(schema)
    db_session.flush()

    assert not schema.has_private

    schema.attributes['is_private'] = models.Attribute(
        name='is_private',
        title=u'',
        type='string',
        is_private=True,
        order=1)

    assert schema.has_private


def test_json(db_session):
    """
    It should be able to load a schema from json data
    """
    import json
    from occams_datastore import models
    schema1 = models.Schema.from_json(json.loads("""
    {
        "name": "sample",
        "title": "Sample",
        "description": null,
        "publish_date": "2000-01-01",
        "storage": "eav",
        "attributes": {
            "section1": {
                "name": "section1",
                "title": "Section 1",
                "description": null,
                "type": "section",
                "order": 0,
                "attributes": {
                    "foo": {
                        "name": "foo",
                        "title": "Foo",
                        "description": null,
                        "type": "choice",
                        "order": 0,
                        "choices": {
                            "001": {
                                "name": "001",
                                "title": "Green",
                                "order": 1
                            },
                            "002": {
                                "name": "002",
                                "title": "Red",
                                "order": 2
                            }
                        }
                    }
                }
            }
        }
    }
    """))
    db_session.add(schema1)
    db_session.flush()

    json.dumps(schema1.to_json())


def test_attribute_defaults(db_session):
    """
    It should set attribute defaults
    """
    from occams_datastore import models

    schema = models.Schema(name=u'Foo', title=u'Foo')
    attribute = models.Attribute(
        schema=schema,
        name=u'foo',
        title=u'Enter Foo',
        type=u'string',
        order=0)
    db_session.add(attribute)
    db_session.flush()
    count = db_session.query(models.Attribute).count()
    assert count, 1 == 'Found more than one entry'


@pytest.mark.parametrize('name', ['5', '5foo', 'foo_5', 'hiv_sex_3'])
def test_attribute_invalid_regexp_name(db_session, name):
    """
    It should prevent invalid attribute names (See RE_VALID_NAME)
    """
    from datetime import date
    from occams_datastore import models

    schema = models.Schema(
        name='SomeForm',
        title=u'Foo',
        publish_date=date(2014, 3, 31))
    db_session.add(schema)
    db_session.flush()

    with pytest.raises(ValueError):
        schema.attributes[name] = models.Attribute(
            name=name,
            title=u'My Attribute',
            type=u'string',
            order=1)


@pytest.mark.parametrize('name', ['f', 'foo', 'foo_', 'foo5'])
def test_attribute_valid_regexp_name(db_session, name):
    """
    It should vallow valid names (See RE_VALID_NAME)
    """
    from datetime import date
    from occams_datastore import models

    schema = models.Schema(
        name='SomeForm',
        title=u'Foo',
        publish_date=date(2014, 3, 31))
    schema.attributes[name] = models.Attribute(
        name=name,
        title=u'My Attribute',
        type=u'string',
        order=1)


def test_attributea_invalid_reserved_name(db_session):
    """
    It should prevent reserved words as attribute names
    """
    from datetime import date
    from occams_datastore import models
    schema = models.Schema(
        name='SomeForm',
        title=u'Foo',
        publish_date=date(2014, 3, 31))
    db_session.add(schema)
    db_session.flush()

    with pytest.raises(ValueError):
        schema.attributes['while'] = models.Attribute(
            name=u'while',
            title=u'My Attribute',
            type=u'string',
            order=1)


def test_attribute_unique_case_insensitive(db_session):
    """
    It should enforce case-insensitive attributes
    """
    from datetime import date
    import sqlalchemy.exc
    from occams_datastore import models

    schema = models.Schema(
        name='Foo',
        title=u'Foo',
        publish_date=date(2014, 3, 31))

    schema.attributes['MyAttr'] = models.Attribute(
        name=u'MyAttr',
        title=u'My Attribute',
        type=u'string',
        order=0)
    db_session.add(schema)
    db_session.flush()

    schema.attributes['myattr'] = models.Attribute(
        name=u'myattr',
        title=u'My Attribute 2',
        type=u'string',
        order=1)

    with pytest.raises(sqlalchemy.exc.IntegrityError):
        db_session.flush()


def test_choice_defaults(db_session):
    """
    It should set choice defaults
    """

    from occams_datastore import models

    schema = models.Schema(name=u'Foo', title=u'Foo')
    attribute = models.Attribute(
        schema=schema,
        name=u'foo',
        title=u'Enter Foo',
        type=u'choice',
        order=0)
    choice1 = models.Choice(
        attribute=attribute, name='001', title=u'Foo', order=0)
    choice2 = models.Choice(
        attribute=attribute, name='002', title=u'Bar', order=1)
    choice3 = models.Choice(
        attribute=attribute, name='003', title=u'Baz', order=2)

    db_session.add_all([schema, attribute, choice1, choice2, choice3])
    db_session.flush()
    count = db_session.query(models.Choice).count()
    assert count, 3 == 'Did not find any choices'


def test_category_defaults(db_session):
    """
    It should set category defaults
    """

    from occams_datastore import models

    category = models.Category(name='Tests', title=u'Test Schemata')
    db_session.add(category)
    db_session.flush()

    count = db_session.query(models.Category).count()
    assert count == 1


def test_add_category_to_schema(db_session):
    """
    Scheamta should be taggable via categories
    """

    from occams_datastore import models

    schema = models.Schema(name='Foo', title=u'')
    db_session.add(schema)
    db_session.flush()

    assert len(schema.categories) == 0
    category1 = models.Category(name='Tests', title=u'Test Schemata')
    schema.categories.add(category1)
    db_session.flush()
    assert len(schema.categories) == 1
    assert len(category1.schemata) == 1
    assert sorted([s.name for s in category1.schemata]) == sorted(['Foo'])

    schema.categories.add(category1)
    db_session.flush()
    assert len(schema.categories) == 1
    assert len(category1.schemata) == 1

    category2 = models.Category(name='Bars', title=u'Bar Schemata')
    schema.categories.add(category2)
    assert len(schema.categories) == 2
    assert sorted([c.name for c in schema.categories]) == \
        sorted(['Tests', 'Bars'])
    assert sorted([s.name for s in category2.schemata]) == sorted(['Foo'])

    # Now try a common use case: get all schema of a certain cateogry
    # First we'll need a second schema of the same category of another
    schema2 = models.Schema(name='Bar', title=u'')
    schema2.categories.add(category2)
    db_session.add(schema2)
    db_session.flush()

    # Now we want all the schemata of a certain category
    schemata = (
        db_session.query(models.Schema)
        .join(models.Schema.categories)
        .filter_by(name='Bars'))

    # Should be the ones we just marked
    assert sorted([s.name for s in schemata]) == \
        sorted(['Foo', 'Bar'])


def test_copy_schema_basic(db_session):
    """
    It should let the user copy schemata
    """
    from copy import deepcopy
    from occams_datastore import models

    schema = models.Schema(
        name='Foo',
        title=u'Foo',
        attributes={
            'section1': models.Attribute(
                name=u'section1',
                title=u'Section 1',
                type='section',
                order=0,
                attributes={
                    'foo': models.Attribute(
                        name='foo',
                        title=u'Enter Foo',
                        type='choice',
                        order=1,
                        choices={
                            '001': models.Choice(
                                name='001', title=u'Foo', order=0),
                            '002': models.Choice(
                                name='002', title=u'Bar', order=1),
                            '003': models.Choice(
                                name='003', title=u'Baz', order=2)},
                        )})})
    db_session.add(schema)
    db_session.flush()

    schema_copy = deepcopy(schema)
    db_session.add(schema_copy)
    db_session.flush()

    # The ones that matter for checksums
    assert schema.name == schema_copy.name
    attribute = schema.attributes['foo']
    for prop in ('name', 'title', 'description', 'type',
                 'is_collection', 'is_required'):
        attribute_copy = schema_copy.attributes['foo']
        assert getattr(attribute, prop) == getattr(attribute_copy, prop)
    for choice in schema.attributes['foo'].choices.values():
        choice_copy = schema_copy.attributes['foo'].choices[choice.name]
        for prop in ('name', 'title', 'order'):
            assert getattr(choice, prop) == getattr(choice_copy, prop)
