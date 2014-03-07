"""
Generate form exports with contextual information.
"""
from sqlalchemy import null

from occams.clinical import Session, models
from occams.clinical.reports._base import Report
from occams.clinical.reports.codebook import types, row
from occams.datastore.reporting import build_report
from occams.datastore.utils.sql import list_concat


class SchemaReport(Report):

    expand_collections = False
    use_choice_labels = False
    ids = None

    @classmethod
    def from_sql(cls, record):
        report = cls()
        report.name = record.name
        report.title = record.title
        report.has_private = record.has_private
        report.has_rand = record.has_rand
        report.versions = record.versions
        return report

    def codebook(self):
        sites_query = Session.query(models.Site) .order_by(models.Site.id)
        states_query = Session.query(models.State).order_by(models.State.id)

        knowns = [
            row('id', self.name, types.NUMERIC, is_required=True),
            row('pid', self.name, types.STRING, is_required=True),
            row('site', self.name, types.CHOICE, is_required=True,
                choices=[(s.id, s.title) for s in sites_query]),
            row('enrollments', self.name, types.STRING, is_collection=True),
            row('cycles', self.name, types.STRING, is_collection=True),
            row('form', self.name, types.STRING, is_required=True),
            row('publish_date', self.name, types.STRING, is_required=True),
            row('state', self.name, types.STRING, is_required=True,
                choices=[(s.id, s.title) for s in states_query]),
            row('collect_date', self.name, types.DATE, is_required=True),
            row('is_null', self.name, types.BOOLEAN, is_required=True),
            row('create_date', self.name, types.DATE, is_required=True),
            row('create_user', self.name, types.STRING, is_required=True),
            row('modify_date', self.name, types.DATE, is_required=True),
            row('modify_user', self.name, types.STRING, is_required=True)]

        for column in knowns:
            yield column

        query = (
            Session.query(models.Attribute)
            .join(models.Schema)
            .filter(models.Schema.name == self.name)
            .filter(models.Schema.publish_date != null())
            .filter(models.Schema.retract_date == null()))

        if self.ids:
            query = query.filter(models.Schema.id.in_(self.ids))

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

    def data(self):
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

        report = build_report(
            Session,
            self.name,
            ids=self.ids,
            expand_collections=self.expand_collections,
            use_choice_labels=self.use_choice_labels)

        query = (
            Session.query(report.c.entity_id.label('id'))
            .add_column(
                Session.query(
                    models.Site.name
                    if self.use_choice_labels else models.Site.id)
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
            .add_columns(
                *[c for c in report.columns if c.name != 'entity_id']))
        return query
