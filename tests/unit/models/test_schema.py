"""
Test case for schema implementations and services
"""

from nose.tools import with_setup

from tests import Session, begin_func, rollback_func


@with_setup(begin_func, rollback_func)
def test_schema_section_attribute():
    """
    It should implement full schema/section/attribute heirarchies
    """
    from datetime import date
    from tests import assert_in
    from occams.datastore import models
    schema = models.Schema(
        name=u'aform',
        title=u'A Form',
        publish_date=date.today(),
        sections={
            'section1': models.Section(
                name=u'section1',
                title=u'Section 1',
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

    Session.add(schema)
    Session.flush()
    assert_in('section1', schema.sections)
    assert_in('foo', schema.attributes)


@with_setup(begin_func, rollback_func)
def test_schema_defaults():
    """
    It should set schema defaults
    """
    from tests import assert_is_none, assert_is_not_none, assert_equals
    from occams.datastore import models

    Session.add(models.Schema(name=u'sample', title=u'Sample'))
    Session.flush()

    schema = Session.query(models.Schema).one()
    assert_is_none(schema.description)
    assert_equals(schema.storage, 'eav')
    assert_is_none(schema.is_association)
    assert_is_not_none(schema.create_date)
    assert_is_not_none(schema.create_user)
    assert_is_not_none(schema.modify_date)
    assert_is_not_none(schema.modify_user)


@with_setup(begin_func, rollback_func)
def test_schema_invalid_regexp_name():
    """
    It should prevent invalid names (See RE_VALID_NAME)
    """
    from datetime import date
    from occams.datastore import models
    from tests import assert_raises
    with assert_raises(ValueError):
        Session.add(models.Schema(
            name='555SomeForm',
            title=u'Foo',
            publish_date=date(2014, 3, 31)))
        Session.flush()


@with_setup(begin_func, rollback_func)
def test_schema_unique_case_insensitive():
    """
    It should enforce case-insensitive schemata
    """
    from tests import assert_raises
    from datetime import date
    import sqlalchemy.exc
    from occams.datastore import models

    Session.add(models.Schema(
        name='Foo',
        title=u'Foo',
        publish_date=date(2014, 3, 31)))
    Session.flush()

    Session.add(models.Schema(
        name='foo',
        title=u'Foo',
        publish_date=date(2014, 3, 31)))

    with assert_raises(sqlalchemy.exc.IntegrityError):
        Session.flush()


@with_setup(begin_func, rollback_func)
def test_schema_publish_date_unique():
    """
    It should enforce unique publish dates
    """

    from tests import assert_raises
    from datetime import date
    import sqlalchemy.exc
    from occams.datastore import models

    # First version
    Session.add(models.Schema(
        name='Foo',
        title=u'Foo',
        publish_date=date(2014, 3, 31)))
    Session.flush()

    # Draft version
    Session.add(models.Schema(
        name='Foo',
        title=u'Foo',
        publish_date=None))
    Session.flush()

    # Add another published schema (not on the same date)
    # Publish, not on the same date
    Session.add(models.Schema(
        name='Foo',
        title=u'Foo',
        publish_date=date(2014, 4, 1)))
    Session.flush()

    # New version, same date (wrong)
    Session.add(models.Schema(
        name='Foo',
        title=u'Foo',
        publish_date=date(2014, 4, 1)))

    with assert_raises(sqlalchemy.exc.IntegrityError):
        Session.flush()


@with_setup(begin_func, rollback_func)
def test_schema_has_private():
    """
    It should be able to determine if a schema has private attributes
    """
    from tests import assert_true, assert_false
    from datetime import date
    from occams.datastore import models
    schema = models.Schema(
        name='Foo',
        title=u'Foo',
        publish_date=date(2014, 3, 31))
    Session.add(schema)
    Session.flush()

    assert_false(schema.has_private)

    section1 = models.Section(
        schema=schema,
        name=u'section1', title=u'Section 1', order=0)

    schema.attributes['not_private'] = models.Attribute(
        schema=schema,
        section=section1,
        name='not_private',
        title=u'',
        type='string',
        is_private=False,
        order=0)

    assert_false(schema.has_private)

    schema.attributes['is_private'] = models.Attribute(
        schema=schema,
        section=section1,
        name='ist_private',
        title=u'',
        type='string',
        is_private=True,
        order=1)

    assert_true(schema.has_private)


@with_setup(begin_func, rollback_func)
def test_json():
    """
    It should be able to load a schema from json data
    """
    import json
    from occams.datastore import models
    schema1 = models.Schema.from_json(json.loads("""
    {
        "name": "sample",
        "title": "Sample",
        "description": null,
        "publish_date": "2000-01-01",
        "storage": "eav",
        "sections": {
            "section1": {
                "name": "section1",
                "title": "Section 1",
                "description": null,
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
    Session.add(schema1)
    Session.flush()

    json.dumps(schema1.to_json())


@with_setup(begin_func, rollback_func)
def test_section_defaults():
    """
    It should set section defaults
    """
    from tests import assert_equals
    from occams.datastore import models

    schema = models.Schema(name='Foo', title=u'Foo')
    section = models.Section(
        schema=schema,
        name='section1',
        title=u'Section 1',
        order=0)
    Session.add_all([schema, section])
    Session.flush()
    count = Session.query(models.Section).count()
    assert_equals(count, 1, 'Found more than one entry')


@with_setup(begin_func, rollback_func)
def test_attribute_defaults():
    """
    It should set attribute defaults
    """
    from tests import assert_equals
    from occams.datastore import models

    schema = models.Schema(name=u'Foo', title=u'Foo')
    section = models.Section(
        schema=schema,
        name=u'section1',
        title=u'Section1',
        order=0)
    attribute = models.Attribute(
        schema=schema,
        section=section,
        name=u'foo',
        title=u'Enter Foo',
        type=u'string',
        order=0)
    Session.add(attribute)
    Session.flush()
    count = Session.query(models.Attribute).count()
    assert_equals(count, 1, 'Found more than one entry')


@with_setup(begin_func, rollback_func)
def test_attributea_invalid_regexp_name():
    """
    It should prevent invalid attribute names (See RE_VALID_NAME)
    """
    from datetime import date
    from occams.datastore import models
    from tests import assert_raises
    schema = models.Schema(
        name='SomeForm',
        title=u'Foo',
        publish_date=date(2014, 3, 31))
    Session.add(schema)
    Session.flush()

    with assert_raises(ValueError):
        schema.attributes['5myattr'] = models.Attribute(
            name=u'5myattr',
            title=u'My Attribute',
            type=u'string',
            order=1)


@with_setup(begin_func, rollback_func)
def test_attributea_invalid_reserved_name():
    """
    It should prevent reserved words as attribute names
    """
    from datetime import date
    from occams.datastore import models
    from tests import assert_raises
    schema = models.Schema(
        name='SomeForm',
        title=u'Foo',
        publish_date=date(2014, 3, 31))
    Session.add(schema)
    Session.flush()

    with assert_raises(ValueError):
        schema.attributes['while'] = models.Attribute(
            name=u'while',
            title=u'My Attribute',
            type=u'string',
            order=1)


@with_setup(begin_func, rollback_func)
def test_attribute_unique_case_insensitive():
    """
    It should enforce case-insensitive attributes
    """
    from tests import assert_raises
    from datetime import date
    import sqlalchemy.exc
    from occams.datastore import models

    schema = models.Schema(
        name='Foo',
        title=u'Foo',
        publish_date=date(2014, 3, 31))

    schema.attributes['MyAttr'] = models.Attribute(
        name=u'MyAttr',
        title=u'My Attribute',
        type=u'string',
        order=0)
    Session.add(schema)
    Session.flush()

    schema.attributes['myattr'] = models.Attribute(
        name=u'myattr',
        title=u'My Attribute 2',
        type=u'string',
        order=1)

    with assert_raises(sqlalchemy.exc.IntegrityError):
        Session.flush()


@with_setup(begin_func, rollback_func)
def test_choice_defaults():
    """
    It should set choice defaults
    """

    from tests import assert_equals
    from occams.datastore import models

    schema = models.Schema(name=u'Foo', title=u'Foo')
    section = models.Section(
        schema=schema,
        name=u'section1',
        title=u'Section1',
        order=0)
    attribute = models.Attribute(
        schema=schema,
        section=section,
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

    Session.add_all([schema, section, attribute, choice1, choice2, choice3])
    Session.flush()
    count = Session.query(models.Choice).count()
    assert_equals(count, 3, 'Did not find any choices')


@with_setup(begin_func, rollback_func)
def test_category_defaults():
    """
    It should set category defaults
    """

    from tests import assert_equals
    from occams.datastore import models

    category = models.Category(name='Tests', title=u'Test Schemata')
    Session.add(category)
    Session.flush()

    count = Session.query(models.Category).count()
    assert_equals(count, 1)


@with_setup(begin_func, rollback_func)
def test_add_category_to_schema():
    """
    Scheamta should be taggable via categories
    """

    from tests import assert_equals, assert_items_equal
    from occams.datastore import models

    schema = models.Schema(name='Foo', title=u'')
    Session.add(schema)
    Session.flush()

    assert_equals(len(schema.categories), 0)
    category1 = models.Category(name='Tests', title=u'Test Schemata')
    schema.categories.add(category1)
    Session.flush()
    assert_equals(len(schema.categories), 1)
    assert_equals(len(category1.schemata), 1)
    assert_items_equal([s.name for s in category1.schemata], ['Foo'])

    schema.categories.add(category1)
    Session.flush()
    assert_equals(len(schema.categories), 1)
    assert_equals(len(category1.schemata), 1)

    category2 = models.Category(name='Bars', title=u'Bar Schemata')
    schema.categories.add(category2)
    assert_equals(len(schema.categories), 2)
    assert_items_equal([c.name for c in schema.categories], ['Tests', 'Bars'])
    assert_items_equal([s.name for s in category2.schemata], ['Foo'])

    # Now try a common use case: get all schema of a certain cateogry
    # First we'll need a second schema of the same category of another
    schema2 = models.Schema(name='Bar', title=u'')
    schema2.categories.add(category2)
    Session.add(schema2)
    Session.flush()

    # Now we want all the schemata of a certain category
    schemata = (
        Session.query(models.Schema)
        .join(models.Schema.categories)
        .filter_by(name='Bars'))

    # Should be the ones we just marked
    assert_items_equal([s.name for s in schemata], ['Foo', 'Bar'])


@with_setup(begin_func, rollback_func)
def test_copy_schema_basic():
    """
    It should let the user copy schemata
    """
    from tests import assert_equals
    from copy import deepcopy
    from occams.datastore import models

    section1 = models.Section(name=u'section1', title=u'Section 1', order=0)
    schema = models.Schema(
        name='Foo',
        title=u'Foo',
        sections={'section1': section1},
        attributes={
            'foo': models.Attribute(
                name='foo',
                title=u'Enter Foo',
                section=section1,
                type='choice',
                choices={
                    '001': models.Choice(name='001', title=u'Foo', order=0),
                    '002': models.Choice(name='002', title=u'Bar', order=1),
                    '003': models.Choice(name='003', title=u'Baz', order=2)},
                order=0)})

    Session.add(schema)
    Session.flush()

    schema_copy = deepcopy(schema)
    Session.add(schema_copy)
    Session.flush()

    # The ones that matter for checksums
    assert_equals(schema.name, schema_copy.name)
    attribute = schema.attributes['foo']
    for prop in ('name', 'title', 'description', 'type',
                 'is_collection', 'is_required'):
        attribute_copy = schema_copy.attributes['foo']
        assert_equals(getattr(attribute, prop), getattr(attribute_copy, prop))
    for choice in schema.attributes['foo'].choices.values():
        choice_copy = schema_copy.attributes['foo'].choices[choice.name]
        for prop in ('name', 'title', 'order'):
            assert_equals(getattr(choice, prop), getattr(choice_copy, prop))
