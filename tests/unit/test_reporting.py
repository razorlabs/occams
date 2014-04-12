"""
Tests the schema report converter module
"""
from nose.tools import with_setup

from tests import Session, begin_func, rollback_func


@with_setup(begin_func, rollback_func)
def test_datadict_published_schema():
    """
    It should only generate a report for published schemata
    """

    from datetime import date, timedelta
    from tests import assert_in, assert_not_in
    from occams.datastore import models, reporting

    schema = models.Schema(
        name=u'A',
        title=u'A',
        sections={
            's1': models.Section(
                name=u's1',
                title=u'S1',
                order=0,
                attributes={
                    'a': models.Attribute(
                        name=u'a',
                        title=u'',
                        type='string',
                        order=0)})})

    Session.add(schema)
    Session.flush()
    columns = reporting.build_columns(Session, u'A')
    assert_not_in('a', columns)

    schema.publish_date = date.today()
    Session.flush()
    columns = reporting.build_columns(Session, u'A')
    assert_in('a', columns)

    schema.retract_date = date.today() + timedelta(1)
    Session.flush()
    columns = reporting.build_columns(Session, u'A')
    assert_not_in('a', columns)


@with_setup(begin_func, rollback_func)
def test_datadict_multpile_versions():
    """
    It should keep track of schema versions while generating column plans
    """

    from copy import deepcopy
    from datetime import date, timedelta
    from tests import assert_in, assert_equals
    from occams.datastore import models, reporting

    today = date.today()

    schema1 = models.Schema(
        name=u'A',
        title=u'A',
        publish_date=today,
        sections={
            's1': models.Section(
                name=u's1',
                title=u'S1',
                order=0,
                attributes={
                    'a': models.Attribute(
                        name=u'a',
                        title=u'',
                        type='string',
                        order=0)})})

    schema2 = deepcopy(schema1)
    schema2.publish_date = today + timedelta(1)

    schema3 = deepcopy(schema2)
    schema3.publish_date = today + timedelta(2)
    schema3.sections['s1'].attributes[u'a'].title = u'prime'

    Session.add_all([schema1, schema2, schema3])
    Session.flush()

    columns = reporting.build_columns(Session, u'A')
    assert_in('a', columns)
    assert_equals(len(columns['a'].attributes), 3)


@with_setup(begin_func, rollback_func)
def test_datadict_multiple_choice():
    """
    It should retain answer choices in the columns dictionary
    """

    from copy import deepcopy
    from datetime import date, timedelta
    from tests import assert_in, assert_items_equal
    from six import iterkeys
    from occams.datastore import models, reporting

    today = date.today()

    schema1 = models.Schema(
        name=u'A',
        title=u'A',
        publish_date=today,
        sections={
            's1': models.Section(
                name=u's1',
                title=u'S1',
                order=0,
                attributes={
                    'a': models.Attribute(
                        name=u'a',
                        title=u'',
                        type='string',
                        is_collection=True,
                        order=0,
                        choices={
                            '001': models.Choice(
                                name=u'001',
                                title=u'Foo',
                                order=0),
                            '002': models.Choice(
                                name=u'002',
                                title=u'Bar',
                                order=1)})})})

    Session.add(schema1)
    Session.flush()

    columns = reporting.build_columns(Session, u'A')
    assert_in('a', columns)
    assert_items_equal(['001', '002'], list(iterkeys(columns['a'].choices)))

    schema2 = deepcopy(schema1)
    schema2.publish_date = today + timedelta(1)
    schema2.sections['s1'].attributes['a'].choices['003'] = \
        models.Choice(name=u'003', title=u'Baz', order=3)
    Session.add(schema2)
    Session.flush()
    columns = reporting.build_columns(Session, u'A')
    assert_items_equal(['001', '002', '003'],
                       list(iterkeys(columns['a'].choices)))


@with_setup(begin_func, rollback_func)
def test_datadict_duplicate_vocabulary_term():
    """
    It should use the most recent version of a choice label
    """

    from copy import deepcopy
    from datetime import date, timedelta
    from tests import assert_equals, assert_in
    from six import itervalues
    from occams.datastore import models, reporting

    today = date.today()

    schema1 = models.Schema(
        name=u'A',
        title=u'A',
        publish_date=today,
        sections={
            's1': models.Section(
                name=u's1',
                title=u'S1',
                order=0,
                attributes={
                    'a': models.Attribute(
                        name=u'a',
                        title=u'',
                        type='string',
                        is_collection=True,
                        order=0,
                        choices={
                            '001': models.Choice(
                                name=u'001',
                                title=u'Foo',
                                order=0),
                            '002': models.Choice(
                                name=u'002',
                                title=u'Bar',
                                order=1)})})})

    schema2 = deepcopy(schema1)
    schema2.state = u'published'
    schema2.publish_date = today + timedelta(1)
    for choice in itervalues(schema2.sections['s1'].attributes['a'].choices):
        choice.title = 'New ' + choice.title

    Session.add_all([schema1, schema2])
    Session.flush()

    columns = reporting.build_columns(Session, u'A')
    assert_in('001', columns['a'].choices)
    assert_in('002', columns['a'].choices)
    assert_equals('New Foo', columns['a'].choices['001'])
    assert_equals('New Bar', columns['a'].choices['002'])


def test_report_column_type():
    """
    It should normalize datastore types to SQL types
    """

    import sqlalchemy as sa

    data = [
        ('choice', sa.String),
        ('string', sa.Unicode),
        ('text', sa.UnicodeText),
        ('integer', sa.Integer),
        ('boolean', sa.Integer),
        ('decimal', sa.Numeric)]

    #### Date/Datetimes aren't easy to test in SQLite...

    for args in data:
        yield tuple([check_report_column_type]) + args


@with_setup(begin_func, rollback_func)
def check_report_column_type(ds_type, sa_type):
    """
    Assert function to check datastore type to sql type conversion
    """

    from datetime import date
    from tests import assert_is_instance
    from occams.datastore import models, reporting

    schema = models.Schema(name=u'A', title=u'A', publish_date=date.today())
    section = models.Section(schema=schema, name=u's1', title=u'S1', order=0)
    attribute = models.Attribute(
        schema=schema, section=section, name=u'a', title=u'', type=ds_type,
        order=0)
    Session.add(attribute)
    Session.flush()

    report = reporting.build_report(Session, u'A')
    column_type = Session.query(report.c.a).column_descriptions[0]['type']

    assert_is_instance(
        column_type,
        sa_type,
        '%s did not covert to %s, got %s'
        % (ds_type, str(sa_type), column_type))


@with_setup(begin_func, rollback_func)
def test_build_report_expected_metadata_columns():
    """
    It should always include entity metdata in the final report query
    """

    from datetime import date
    from tests import assert_in
    from occams.datastore import models, reporting

    today = date.today()

    schema = models.Schema(name=u'A', title=u'A', publish_date=today)
    Session.add(schema)
    Session.flush()

    report = reporting.build_report(Session, u'A')
    assert_in(u'id', report.c)
    assert_in(u'form', report.c)
    assert_in(u'publish_date', report.c)
    assert_in(u'state', report.c)
    assert_in(u'collect_date', report.c)
    assert_in(u'is_null', report.c)
    assert_in(u'create_date', report.c)
    assert_in(u'create_user', report.c)
    assert_in(u'modify_date', report.c)
    assert_in(u'modify_user', report.c)


@with_setup(begin_func, rollback_func)
def test_build_report_scalar_values():
    """
    It should properly report scalar values
    """

    from datetime import date
    from tests import assert_equals
    from occams.datastore import models, reporting

    today = date.today()

    schema1 = models.Schema(
        name=u'A',
        title=u'A',
        publish_date=today,
        sections={
            's1': models.Section(
                name=u's1',
                title=u'S1',
                order=0,
                attributes={
                    'a': models.Attribute(
                        name=u'a',
                        title=u'',
                        type='string',
                        order=0)})})

    Session.add(schema1)
    Session.flush()

    # add some entries for the schema
    entity1 = models.Entity(schema=schema1, name=u'Foo', title=u'')
    entity1['a'] = u'foovalue'
    Session.add(entity1)
    Session.flush()

    report = reporting.build_report(Session, u'A')
    result = Session.query(report).one()
    assert_equals(entity1[u'a'], result.a)


@with_setup(begin_func, rollback_func)
def test_build_report_datetime():
    """
    It should be able to cast DATE/DATETIME
    """
    from datetime import date
    from tests import assert_equals
    from occams.datastore import models, reporting

    today = date.today()

    schema1 = models.Schema(
        name=u'A',
        title=u'A',
        publish_date=today,
        sections={
            's1': models.Section(
                name=u's1',
                title=u'S1',
                order=0,
                attributes={
                    'a': models.Attribute(
                        name=u'a',
                        title=u'',
                        type='date',
                        order=0)})})
    Session.add(schema1)
    Session.flush()

    # add some entries for the schema
    entity1 = models.Entity(schema=schema1, name=u'Foo', title=u'')
    entity1['a'] = date(1976, 7, 4)
    Session.add(entity1)
    Session.flush()

    report = reporting.build_report(Session, u'A')
    result = Session.query(report).one()
    assert_equals(str(result.a), '1976-07-04')

    schema1.sections['s1'].attributes['a'].type = 'datetime'
    Session.flush()
    report = reporting.build_report(Session, u'A')
    result = Session.query(report).one()
    assert_equals(str(result.a), '1976-07-04 00:00:00')


@with_setup(begin_func, rollback_func)
def test_build_report_choice_types():
    """
    It should be able to use choice labels instead of codes.
    (for human readibily)
    """

    from datetime import date
    from tests import assert_is_none, assert_equals, assert_items_equal
    from occams.datastore import models, reporting

    today = date.today()

    schema1 = models.Schema(
        name=u'A',
        title=u'A',
        publish_date=today,
        sections={
            's1': models.Section(
                name=u's1',
                title=u'S1',
                order=0,
                attributes={
                    'a': models.Attribute(
                        name=u'a',
                        title=u'',
                        type='choice',
                        is_collection=False,
                        order=0,
                        choices={
                            '001': models.Choice(
                                name=u'001',
                                title=u'Green',
                                order=0),
                            '002': models.Choice(
                                name=u'002',
                                title=u'Red',
                                order=1),
                            '003': models.Choice(
                                name=u'003',
                                title=u'Blue',
                                order=2)
                            })})})
    Session.add(schema1)
    Session.flush()

    entity1 = models.Entity(schema=schema1, name=u'Foo', title=u'')
    entity1['a'] = u'002'
    Session.add(entity1)
    Session.flush()

    # labels off
    report = reporting.build_report(Session, u'A', use_choice_labels=False)
    result = Session.query(report).one()
    assert_equals(result.a, '002')

    # labels on
    report = reporting.build_report(Session, u'A', use_choice_labels=True)
    result = Session.query(report).one()
    assert_equals(result.a, 'Red')

    # switch to multiple-choice
    schema1.attributes['a'].is_collection = True
    entity1['a'] = ['002', '003']
    Session.flush()

    # delimited multiple-choice, labels off
    report = reporting.build_report(Session, u'A',
                                    expand_collections=False,
                                    use_choice_labels=False)
    result = Session.query(report).one()
    assert_items_equal(result.a.split(';'), ['002', '003'])

    # delimited multiple-choice, labels on
    report = reporting.build_report(Session, u'A',
                                    expand_collections=False,
                                    use_choice_labels=True)
    result = Session.query(report).one()
    assert_items_equal(result.a.split(';'), ['Red', 'Blue'])

    # expanded multiple-choice, labels off
    report = reporting.build_report(Session, u'A',
                                    expand_collections=True,
                                    use_choice_labels=False)
    result = Session.query(report).one()
    assert_equals(result.a_001, 0)
    assert_equals(result.a_002, 1)
    assert_equals(result.a_003, 1)

    # expanded multiple-choice, labels on
    report = reporting.build_report(Session, u'A',
                                    expand_collections=True,
                                    use_choice_labels=True)
    result = Session.query(report).one()
    assert_is_none(result.a_001)
    assert_equals(result.a_002, 'Red')
    assert_equals(result.a_003, 'Blue')


@with_setup(begin_func, rollback_func)
def test_build_report_expand_none_selected():
    """
    It should leave all choices blank (not zero) on if no option was selected
    """
    from datetime import date
    from tests import assert_is_none, assert_equals, assert_items_equal
    from occams.datastore import models, reporting

    today = date.today()

    schema1 = models.Schema(
        name=u'A',
        title=u'A',
        publish_date=today,
        sections={
            's1': models.Section(
                name=u's1',
                title=u'S1',
                order=0,
                attributes={
                    'a': models.Attribute(
                        name=u'a',
                        title=u'',
                        type='choice',
                        is_collection=True,
                        order=0,
                        choices={
                            '001': models.Choice(
                                name=u'001',
                                title=u'Green',
                                order=0),
                            '002': models.Choice(
                                name=u'002',
                                title=u'Red',
                                order=1),
                            '003': models.Choice(
                                name=u'003',
                                title=u'Blue',
                                order=2)
                            })})})
    Session.add(schema1)
    Session.flush()

    entity1 = models.Entity(schema=schema1, name=u'Foo', title=u'')
    Session.add(entity1)
    Session.flush()

    # delimited multiple-choice, labels off
    report = reporting.build_report(Session, u'A',
                                    expand_collections=False,
                                    use_choice_labels=False)
    result = Session.query(report).one()
    assert_is_none(result.a)

    # delimited multiple-choice, labels on
    report = reporting.build_report(Session, u'A',
                                    expand_collections=False,
                                    use_choice_labels=True)
    result = Session.query(report).one()
    assert_is_none(result.a)

    # expanded multiple-choice, labels off
    report = reporting.build_report(Session, u'A',
                                    expand_collections=True,
                                    use_choice_labels=False)
    result = Session.query(report).one()
    assert_is_none(result.a_001)
    assert_is_none(result.a_002)
    assert_is_none(result.a_003)

    # expanded multiple-choice, labels on
    report = reporting.build_report(Session, u'A',
                                    expand_collections=True,
                                    use_choice_labels=True)
    result = Session.query(report).one()
    assert_is_none(result.a_001)
    assert_is_none(result.a_002)
    assert_is_none(result.a_003)


@with_setup(begin_func, rollback_func)
def test_build_report_ids():
    """
    It should be able to include only the schemata with the specified ids
    """

    from copy import deepcopy
    from datetime import date, timedelta
    from tests import assert_in, assert_not_in
    from occams.datastore import models, reporting

    today = date.today()

    schema1 = models.Schema(
        name=u'A',
        title=u'A',
        publish_date=today,
        sections={
            's1': models.Section(
                name=u's1',
                title=u'S1',
                order=0,
                attributes={
                    'a': models.Attribute(
                        name=u'a',
                        title=u'',
                        type='string',
                        is_private=True,
                        order=0)})})
    Session.add(schema1)
    Session.flush()

    schema2 = deepcopy(schema1)
    schema2.publish_date = today + timedelta(1)
    schema2.sections['s1'].attributes['b'] = models.Attribute(
        name=u'b',
        title=u'',
        type='string',
        is_private=True,
        order=1)
    Session.add(schema2)
    Session.flush()

    # all
    report = reporting.build_report(Session, u'A')
    assert_in('a', report.c)
    assert_in('b', report.c)

    # Only v1
    report = reporting.build_report(Session, u'A', ids=[schema1.id])
    assert_in('a', report.c)
    assert_not_in('b', report.c)


@with_setup(begin_func, rollback_func)
def test_build_report_context():
    """
    It should be able to associate with a context. (for easier joins)
    """

    from datetime import date
    from tests import assert_in, assert_not_in, assert_equals
    from occams.datastore import models, reporting

    today = date.today()

    schema1 = models.Schema(
        name=u'A',
        title=u'A',
        publish_date=today,
        sections={
            's1': models.Section(
                name=u's1',
                title=u'S1',
                order=0,
                attributes={
                    'a': models.Attribute(
                        name=u'a',
                        title=u'',
                        type='string',
                        is_private=True,
                        order=0)})})
    Session.add(schema1)
    Session.flush()

    entity1 = models.Entity(schema=schema1, name=u'Foo', title=u'')
    entity1['a'] = u'002'
    Session.add(entity1)
    Session.flush()

    Session.add(models.Context(external='sometable', key=123, entity=entity1))
    Session.flush()

    # not specified
    report = reporting.build_report(Session, u'A')
    assert_not_in('context_key', report.c)

    # specified
    report = reporting.build_report(Session, u'A', context='sometable')
    result = Session.query(report).one()
    assert_in('context_key', report.c)
    assert_equals(result.context_key, 123)


@with_setup(begin_func, rollback_func)
def test_build_report_attributes():
    """
    It should only include the specified columns (useful for large forms)
    """
    from datetime import date
    from tests import assert_in, assert_not_in
    from occams.datastore import models, reporting

    today = date.today()

    schema1 = models.Schema(
        name=u'A',
        title=u'A',
        publish_date=today,
        sections={
            's1': models.Section(
                name=u's1',
                title=u'S1',
                order=0,
                attributes={
                    'a': models.Attribute(
                        name=u'a',
                        title=u'',
                        type='string',
                        is_private=True,
                        order=0),
                    'b': models.Attribute(
                        name=u'b',
                        title=u'',
                        type='string',
                        is_private=True,
                        order=1)})})

    Session.add(schema1)
    Session.flush()

    report = reporting.build_report(Session, u'A', attributes=['b'])
    assert_not_in('a', report.c)
    assert_in('b', report.c)


@with_setup(begin_func, rollback_func)
def test_build_report_ignore_private():
    """
    It should be able to de-identify private data upon request
    """

    from datetime import date
    from tests import assert_equals
    from occams.datastore import models, reporting

    today = date.today()

    schema1 = models.Schema(
        name=u'A',
        title=u'A',
        publish_date=today,
        sections={
            's1': models.Section(
                name=u's1',
                title=u'S1',
                order=0,
                attributes={
                    'name': models.Attribute(
                        name=u'name',
                        title=u'',
                        type='string',
                        is_private=True,
                        order=0)})})

    Session.add(schema1)
    Session.flush()

    # add some entries for the schema
    entity1 = models.Entity(schema=schema1, name=u'Foo', title=u'')
    entity1['name'] = u'Jane Doe'
    Session.add(entity1)
    Session.flush()

    # not de-identified
    report = reporting.build_report(Session, u'A', ignore_private=False)
    result = Session.query(report).one()
    assert_equals(entity1[u'name'], result.name)

    # de-identified
    report = reporting.build_report(Session, u'A', ignore_private=True)
    result = Session.query(report).one()
    assert_equals('[PRIVATE]', result.name)
