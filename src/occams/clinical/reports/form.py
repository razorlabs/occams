from sqlalchemy import null

from occams.clinical import Session, models
from occams.clinical.reports.codebook import types, row
from occams.datastore.reporting import build_report
from occams.datastore.utils.sql import list_concat


def codebook(schema_name, ids=None):
    sites_query = Session.query(models.Site) .order_by(models.Site.id)
    states_query = Session.query(models.State).order_by(models.State.id)

    knowns = [
        row('id', schema_name, types.NUMERIC, is_required=True),
        row('pid', schema_name, types.STRING, is_required=True),
        row('site', schema_name, types.CHOICE, is_required=True,
            choices=[(s.id, s.title) for s in sites_query]),
        row('enrollments', schema_name, types.STRING, is_collection=True),
        row('cycles', schema_name, types.STRING, is_collection=True),
        row('form', schema_name, types.STRING, is_required=True),
        row('publish_date', schema_name, types.STRING, is_required=True),
        row('state', schema_name, types.STRING, is_required=True,
            choices=[(s.id, s.title) for s in states_query]),
        row('collect_date', schema_name, types.DATE, is_required=True),
        row('is_null', schema_name, types.BOOLEAN, is_required=True),
        row('create_date', schema_name, types.DATE, is_required=True),
        row('create_user', schema_name, types.STRING, is_required=True),
        row('modify_date', schema_name, types.DATE, is_required=True),
        row('modify_user', schema_name, types.STRING, is_required=True)]

    for column in knowns:
        yield column

    query = (
        Session.query(models.Attribute)
        .join(models.Schema)
        .filter(models.Schema.name == schema_name)
        .filter(models.Schema.publish_date != null())
        .filter(models.Schema.retract_date == null()))

    if ids:
        query = query.filter(models.Schema.id.in_(ids))

    query = (
        query.order_by(
            models.Attribute.order,
            models.Schema.publish_date))

    for attribute in query:
        yield row(attribute.name, attribute.schema.name, attribute.type,
                  form=attribute.schema.title,
                  publish_date=attribute.schema.publish_date,
                  title=attribute.title,
                  desc=attribute.description,
                  is_required=attribute.is_required,
                  is_collection=attribute.is_collection,
                  order=attribute.order,
                  is_private=attribute.is_private,
                  choices=[(c.name, c.title) for c in attribute.choices])


def query_report(schema_name,
                 ids,
                 expand_collections=False,
                 use_choice_labels=False):
    """
    Generates a clinical report containing the patient's metadata
    that relates to the form.

    Clinical metadadata includes:
        * site -- Patient's site
        * pid -- Patient's PID number
        * enrollment -- The applicable enrollment
        * cycles - The applicable visit's cycles

    Parameters:
    schema -- The schema to generate the report for

    Returns:
    A SQLAlchemy query
    """

    report = build_report(Session, schema_name, ids,
                          expand_collections=expand_collections,
                          use_choice_labels=use_choice_labels)

    query = (
        Session.query(report.c.entity_id.label('id'))
        .add_column(
            Session.query(
                models.Site.name if use_choice_labels else models.Site.id)
            .select_from(models.Patient)
            .join(models.Site)
            .join(models.Context,
                  (models.Context.external == 'patient')
                  & (models.Context.key == models.Patient.id))
            .filter(models.Context.entity_id == report.c.entity_id)
            .correlate(report)
            .as_scalar()
            .label('site'))
        .add_column(
            Session.query(models.Patient.pid)
            .join(models.Context,
                  (models.Context.external == 'patient')
                  & (models.Context.key == models.Patient.id))
            .filter(models.Context.entity_id == report.c.entity_id)
            .correlate(report)
            .as_scalar()
            .label('pid'))
        .add_column(
            list_concat(
                Session.query(models.Study.name)
                .select_from(models.Enrollment)
                .join(models.Study)
                .join(models.Context,
                      (models.Context.external == 'enrollment')
                      & (models.Context.key == models.Enrollment.id))
                .filter(models.Context.entity_id == report.c.entity_id)
                .correlate(report)
                .as_scalar(), ';')
            .label('enrollment'))
        .add_column(
            list_concat(
                Session.query(models.Cycle.name)
                .select_from(models.Visit)
                .join(models.Visit.cycles)
                .join(models.Context,
                      (models.Context.external == 'visit')
                      & (models.Context.key == models.Visit.id))
                .filter(models.Context.entity_id == report.c.entity_id)
                .correlate(report)
                .as_scalar(), ';')
            .label('cycles'))
        .add_columns(*[c for c in report.columns if c.name != 'entity_id']))
    return query

