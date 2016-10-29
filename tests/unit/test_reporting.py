"""
Tests the schema report converter module
"""

import pytest
import sqlalchemy as sa


def test_datadict_published_schema(dbsession):
    """
    It should only generate a report for published schemata
    """

    from datetime import date, timedelta
    from occams_datastore import models, reporting

    schema = models.Schema(
        name=u'A',
        title=u'A',
        attributes={
            's1': models.Attribute(
                name=u's1',
                title=u'S1',
                type='section',
                order=0,
                attributes={
                    'a': models.Attribute(
                        name=u'a',
                        title=u'',
                        type='string',
                        order=0)})})

    dbsession.add(schema)
    dbsession.flush()
    columns = reporting.build_columns(dbsession, u'A')
    assert 'a' not in columns

    schema.publish_date = date.today()
    dbsession.flush()
    columns = reporting.build_columns(dbsession, u'A')
    assert 'a' in columns

    schema.retract_date = date.today() + timedelta(1)
    dbsession.flush()
    columns = reporting.build_columns(dbsession, u'A')
    assert 'a' not in columns


def test_datadict_multpile_versions(dbsession):
    """
    It should keep track of schema versions while generating column plans
    """

    from copy import deepcopy
    from datetime import date, timedelta
    from occams_datastore import models, reporting

    today = date.today()

    schema1 = models.Schema(
        name=u'A',
        title=u'A',
        publish_date=today,
        attributes={
            's1': models.Attribute(
                name=u's1',
                title=u'S1',
                type='section',
                order=0,
                attributes={
                    'a': models.Attribute(
                        name=u'a',
                        title=u'',
                        type='string',
                        order=1)})})

    schema2 = deepcopy(schema1)
    schema2.publish_date = today + timedelta(1)

    schema3 = deepcopy(schema2)
    schema3.publish_date = today + timedelta(2)
    schema3.attributes['s1'].attributes['a'].title = u'prime'

    dbsession.add_all([schema1, schema2, schema3])
    dbsession.flush()

    columns = reporting.build_columns(dbsession, u'A')
    assert 'a' in columns
    assert len(columns['a'].attributes) == 3


def test_datadict_multiple_choice(dbsession):
    """
    It should retain answer choices in the columns dictionary
    """

    from copy import deepcopy
    from datetime import date, timedelta
    from six import iterkeys
    from occams_datastore import models, reporting

    today = date.today()

    schema1 = models.Schema(
        name=u'A',
        title=u'A',
        publish_date=today,
        attributes={
            's1': models.Attribute(
                name=u's1',
                title=u'S1',
                type='section',
                order=0,
                attributes={
                    'a': models.Attribute(
                        name=u'a',
                        title=u'',
                        type='string',
                        is_collection=True,
                        order=1,
                        choices={
                            '001': models.Choice(
                                name=u'001',
                                title=u'Foo',
                                order=0),
                            '002': models.Choice(
                                name=u'002',
                                title=u'Bar',
                                order=1)})})})

    dbsession.add(schema1)
    dbsession.flush()

    columns = reporting.build_columns(dbsession, u'A')
    assert 'a' in columns
    assert sorted(['001', '002']) == sorted(iterkeys(columns['a'].choices))

    schema2 = deepcopy(schema1)
    schema2.publish_date = today + timedelta(1)
    schema2.attributes['s1'].attributes['a'].choices['003'] = \
        models.Choice(name=u'003', title=u'Baz', order=3)
    dbsession.add(schema2)
    dbsession.flush()
    columns = reporting.build_columns(dbsession, u'A')
    assert sorted(['001', '002', '003']) == \
        sorted(iterkeys(columns['a'].choices))


def test_datadict_duplicate_vocabulary_term(dbsession):
    """
    It should use the most recent version of a choice label
    """

    from copy import deepcopy
    from datetime import date, timedelta
    from six import itervalues
    from occams_datastore import models, reporting

    today = date.today()

    schema1 = models.Schema(
        name=u'A',
        title=u'A',
        publish_date=today,
        attributes={
            's1': models.Attribute(
                name=u's1',
                title=u'S1',
                type='section',
                order=0,
                attributes={
                    'a': models.Attribute(
                        name=u'a',
                        title=u'',
                        type='string',
                        is_collection=True,
                        order=1,
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
    for choice in itervalues(schema2.attributes['s1'].attributes['a'].choices):
        choice.title = 'New ' + choice.title

    dbsession.add_all([schema1, schema2])
    dbsession.flush()

    columns = reporting.build_columns(dbsession, u'A')
    assert '001' in columns['a'].choices
    assert '002' in columns['a'].choices
    assert 'New Foo' == columns['a'].choices['001']
    assert 'New Bar' == columns['a'].choices['002']


@pytest.mark.parametrize('db_type,sa_type', [
    ('choice', sa.String),
    ('string', sa.Unicode),
    ('text', sa.UnicodeText),
    ('number', sa.Numeric)
])
def check_report_column_type(dbsession, ds_type, sa_type):
    """
    It should normalize datastore types to SQL types
    """

    from datetime import date
    from occams_datastore import models, reporting

    schema = models.Schema(
        name=u'A',
        title=u'A',
        publish_date=date.today(),
        attributes={
            's1': models.Attribute(
                name=u's1',
                title=u'S1',
                type='section',
                order=0,
                attributes={
                    'a': models.Attribute(
                        name=u'a',
                        title=u'',
                        type=ds_type,
                        order=1)})})
    dbsession.add(schema)
    dbsession.flush()

    report = reporting.build_report(dbsession, u'A')
    column_type = dbsession.query(report.c.a).column_descriptions[0]['type']

    assert isinstance(column_type, sa_type), \
        '%s did not covert to %s, got %s' \
        % (ds_type, str(sa_type), column_type)


def test_build_report_expected_metadata_columns(dbsession):
    """
    It should always include entity metdata in the final report query
    """

    from datetime import date
    from occams_datastore import models, reporting

    today = date.today()

    schema = models.Schema(name=u'A', title=u'A', publish_date=today)
    dbsession.add(schema)
    dbsession.flush()

    report = reporting.build_report(dbsession, u'A')
    assert u'id' in report.c
    assert u'form_name' in report.c
    assert u'form_publish_date' in report.c
    assert u'state' in report.c
    assert u'collect_date' in report.c
    assert u'not_done' in report.c
    assert u'create_date' in report.c
    assert u'create_user' in report.c
    assert u'modify_date' in report.c
    assert u'modify_user' in report.c


def test_build_report_scalar_values(dbsession):
    """
    It should properly report scalar values
    """

    from datetime import date
    from occams_datastore import models, reporting

    today = date.today()

    schema1 = models.Schema(
        name=u'A',
        title=u'A',
        publish_date=today,
        attributes={
            's1': models.Attribute(
                name=u's1',
                title=u'S1',
                type='section',
                order=0,
                attributes={
                    'a': models.Attribute(
                        name=u'a',
                        title=u'',
                        type='string',
                        order=1)})})

    dbsession.add(schema1)
    dbsession.flush()

    # add some entries for the schema
    entity1 = models.Entity(schema=schema1)
    entity1['a'] = u'foovalue'
    dbsession.add(entity1)
    dbsession.flush()

    report = reporting.build_report(dbsession, u'A')
    result = dbsession.query(report).one()
    assert entity1[u'a'] == result.a


def test_build_report_datetime(dbsession):
    """
    It should be able to cast DATE/DATETIME
    """
    from datetime import date
    from occams_datastore import models, reporting

    today = date.today()

    schema1 = models.Schema(
        name=u'A',
        title=u'A',
        publish_date=today,
        attributes={
            's1': models.Attribute(
                name=u's1',
                title=u'S1',
                type='section',
                order=0,
                attributes={
                    'a': models.Attribute(
                        name=u'a',
                        title=u'',
                        type='date',
                        order=1)})})
    dbsession.add(schema1)
    dbsession.flush()

    # add some entries for the schema
    entity1 = models.Entity(schema=schema1)
    entity1['a'] = date(1976, 7, 4)
    dbsession.add(entity1)
    dbsession.flush()

    report = reporting.build_report(dbsession, u'A')
    result = dbsession.query(report).one()
    assert str(result.a) == '1976-07-04'

    schema1.attributes['s1'].attributes['a'].type = 'datetime'
    dbsession.flush()
    report = reporting.build_report(dbsession, u'A')
    result = dbsession.query(report).one()
    assert str(result.a) == '1976-07-04 00:00:00'


def test_build_report_choice_types(dbsession):
    """
    It should be able to use choice labels instead of codes.
    (for human readibily)
    """

    from datetime import date
    from occams_datastore import models, reporting

    today = date.today()

    schema1 = models.Schema(
        name=u'A',
        title=u'A',
        publish_date=today,
        attributes={
            's1': models.Attribute(
                name=u's1',
                title=u'S1',
                type='section',
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
    dbsession.add(schema1)
    dbsession.flush()

    entity1 = models.Entity(schema=schema1)
    entity1['a'] = u'002'
    dbsession.add(entity1)
    dbsession.flush()

    # labels off
    report = reporting.build_report(dbsession, u'A', use_choice_labels=False)
    result = dbsession.query(report).one()
    assert result.a == '002'

    # labels on
    report = reporting.build_report(dbsession, u'A', use_choice_labels=True)
    result = dbsession.query(report).one()
    assert result.a == 'Red'

    # switch to multiple-choice
    schema1.attributes['a'].is_collection = True
    entity1['a'] = ['002', '003']
    dbsession.flush()

    # delimited multiple-choice, labels off
    report = reporting.build_report(dbsession, u'A',
                                    expand_collections=False,
                                    use_choice_labels=False)
    result = dbsession.query(report).one()
    assert sorted(result.a.split(';')) == sorted(['002', '003'])

    # delimited multiple-choice, labels on
    report = reporting.build_report(dbsession, u'A',
                                    expand_collections=False,
                                    use_choice_labels=True)
    result = dbsession.query(report).one()
    assert sorted(result.a.split(';')) == sorted(['Red', 'Blue'])

    # expanded multiple-choice, labels off
    report = reporting.build_report(dbsession, u'A',
                                    expand_collections=True,
                                    use_choice_labels=False)
    result = dbsession.query(report).one()
    assert result.a_001 == 0
    assert result.a_002 == 1
    assert result.a_003 == 1

    # expanded multiple-choice, labels on
    report = reporting.build_report(dbsession, u'A',
                                    expand_collections=True,
                                    use_choice_labels=True)
    result = dbsession.query(report).one()
    assert result.a_001 is None
    assert result.a_002 == 'Red'
    assert result.a_003 == 'Blue'


def test_build_report_expand_none_selected(dbsession):
    """
    It should leave all choices blank (not zero) on if no option was selected
    """
    from datetime import date
    from occams_datastore import models, reporting

    today = date.today()

    schema1 = models.Schema(
        name=u'A',
        title=u'A',
        publish_date=today,
        attributes={
            's1': models.Attribute(
                name=u's1',
                title=u'S1',
                type='section',
                order=0,
                attributes={
                    'a': models.Attribute(
                        name=u'a',
                        title=u'',
                        type='choice',
                        is_collection=True,
                        order=1,
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
    dbsession.add(schema1)
    dbsession.flush()

    entity1 = models.Entity(schema=schema1)
    dbsession.add(entity1)
    dbsession.flush()

    # delimited multiple-choice, labels off
    report = reporting.build_report(dbsession, u'A',
                                    expand_collections=False,
                                    use_choice_labels=False)
    result = dbsession.query(report).one()
    assert result.a is None

    # delimited multiple-choice, labels on
    report = reporting.build_report(dbsession, u'A',
                                    expand_collections=False,
                                    use_choice_labels=True)
    result = dbsession.query(report).one()
    assert result.a is None

    # expanded multiple-choice, labels off
    report = reporting.build_report(dbsession, u'A',
                                    expand_collections=True,
                                    use_choice_labels=False)
    result = dbsession.query(report).one()
    assert result.a_001 is None
    assert result.a_002 is None
    assert result.a_003 is None

    # expanded multiple-choice, labels on
    report = reporting.build_report(dbsession, u'A',
                                    expand_collections=True,
                                    use_choice_labels=True)
    result = dbsession.query(report).one()
    assert result.a_001 is None
    assert result.a_002 is None
    assert result.a_003 is None


def test_build_report_ids(dbsession):
    """
    It should be able to include only the schemata with the specified ids
    """

    from copy import deepcopy
    from datetime import date, timedelta
    from occams_datastore import models, reporting

    today = date.today()

    schema1 = models.Schema(
        name=u'A',
        title=u'A',
        publish_date=today,
        attributes={
            's1': models.Attribute(
                name=u's1',
                title=u'S1',
                type='section',
                order=0,
                attributes={
                    'a': models.Attribute(
                        name=u'a',
                        title=u'',
                        type='string',
                        is_private=True,
                        order=1)})})
    dbsession.add(schema1)
    dbsession.flush()

    schema2 = deepcopy(schema1)
    schema2.publish_date = today + timedelta(1)
    schema2.attributes['s1'].attributes['b'] = models.Attribute(
        name=u'b',
        title=u'',
        type='string',
        is_private=True,
        order=1)
    dbsession.add(schema2)
    dbsession.flush()

    # all
    report = reporting.build_report(dbsession, u'A')
    assert 'a' in report.c
    assert 'b' in report.c

    # Only v1
    report = reporting.build_report(dbsession, u'A', ids=[schema1.id])
    assert 'a' in report.c
    assert 'b' not in report.c


def test_build_report_context(dbsession):
    """
    It should be able to associate with a context. (for easier joins)
    """

    from datetime import date
    from occams_datastore import models, reporting

    today = date.today()

    schema1 = models.Schema(
        name=u'A',
        title=u'A',
        publish_date=today,
        attributes={
            's1': models.Attribute(
                name=u's1',
                title=u'S1',
                type='section',
                order=0,
                attributes={
                    'a': models.Attribute(
                        name=u'a',
                        title=u'',
                        type='string',
                        is_private=True,
                        order=1)})})
    dbsession.add(schema1)
    dbsession.flush()

    entity1 = models.Entity(schema=schema1)
    entity1['a'] = u'002'
    dbsession.add(entity1)
    dbsession.flush()

    dbsession.add(
        models.Context(external='sometable', key=123, entity=entity1))
    dbsession.flush()

    # not specified
    report = reporting.build_report(dbsession, u'A')
    assert 'context_key' not in report.c

    # specified
    report = reporting.build_report(dbsession, u'A', context='sometable')
    result = dbsession.query(report).one()
    assert 'context_key' in report.c
    assert result.context_key == 123


def test_build_report_attributes(dbsession):
    """
    It should only include the specified columns (useful for large forms)
    """
    from datetime import date
    from occams_datastore import models, reporting

    today = date.today()

    schema1 = models.Schema(
        name=u'A',
        title=u'A',
        publish_date=today,
        attributes={
            's1': models.Attribute(
                name=u's1',
                title=u'S1',
                type='section',
                order=0,
                attributes={
                    'a': models.Attribute(
                        name=u'a',
                        title=u'',
                        type='string',
                        is_private=True,
                        order=1),
                    'b': models.Attribute(
                        name=u'b',
                        title=u'',
                        type='string',
                        is_private=True,
                        order=2)})})

    dbsession.add(schema1)
    dbsession.flush()

    report = reporting.build_report(dbsession, u'A', attributes=['b'])
    assert 'a' not in report.c
    assert 'b' in report.c


def test_build_report_ignore_private(dbsession):
    """
    It should be able to de-identify private data upon request
    """

    from datetime import date
    from occams_datastore import models, reporting

    today = date.today()

    schema1 = models.Schema(
        name=u'A',
        title=u'A',
        publish_date=today,
        attributes={
            's1': models.Attribute(
                name=u's1',
                title=u'S1',
                type='section',
                order=0,
                attributes={
                    'name': models.Attribute(
                        name=u'name',
                        title=u'',
                        type='string',
                        is_private=True,
                        order=1)})})

    dbsession.add(schema1)
    dbsession.flush()

    # add some entries for the schema
    entity1 = models.Entity(schema=schema1)
    entity1['name'] = u'Jane Doe'
    dbsession.add(entity1)
    dbsession.flush()

    # not de-identified
    report = reporting.build_report(dbsession, u'A', ignore_private=False)
    result = dbsession.query(report).one()
    assert entity1[u'name'] == result.name

    # de-identified
    report = reporting.build_report(dbsession, u'A', ignore_private=True)
    result = dbsession.query(report).one()
    assert '[PRIVATE]' == result.name
