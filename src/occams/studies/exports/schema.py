"""
Generate form exports with contextual information.

Also incorporates:
    avrcdataexport/sql/UsableRandomization594.sql
    avrcdataexport/sql/UsableRandomization595.sql
    avrcdataexport/sql/UsableRandomization599.sql

"""

from datetime import datetime
from six import itervalues
from sqlalchemy import orm, null, cast, String, literal_column

from occams.datastore.reporting import build_report
from occams.datastore.utils.sql import group_concat, to_date

from .. import Session, models
from .plan import ExportPlan
from .codebook import types, row


class SchemaPlan(ExportPlan):

    @classmethod
    def from_sql(cls, record):
        """
        Creates a plan instance from an internal query inspection
        """
        report = cls()
        report.name = record.name
        report.title = record.title
        report.has_private = record.has_private
        report.has_rand = record.has_rand
        report.versions = sorted([datetime.strptime(v, '%Y-%m-%d').date()
                                  for v in record.versions.split(';')])
        return report

    @classmethod
    def from_schema(cls, name):
        """
        Creates a plan from a schema name
        """
        subquery = cls._query().subquery()
        query = Session.query(subquery).filter(subquery.c.name == name)
        return cls.from_sql(query.one())

    @classmethod
    def _query(self):
        InnerSchema = orm.aliased(models.Schema)
        OuterSchema = orm.aliased(models.Schema)

        schemata_query = (
            Session.query(OuterSchema.name.label('name'))
            .add_column(literal_column("'schema'").label('type'))
            .add_column(
                Session.query(models.Attribute)
                .filter(models.Attribute.is_private)
                .join(InnerSchema)
                .filter(InnerSchema.name == OuterSchema.name)
                .correlate(OuterSchema)
                .exists()
                .label('has_private'))
            .add_column(
                Session.query(models.Entity)
                .join(models.Entity.contexts)
                .filter(models.Context.external == 'stratum')
                .join(models.Stratum, models.Context.key == models.Stratum.id)
                .join(InnerSchema, models.Entity.schema)
                .filter(InnerSchema.name == OuterSchema.name)
                .correlate(OuterSchema)
                .exists()
                .label('has_rand'))
            .add_column(
                Session.query(InnerSchema.title)
                .select_from(InnerSchema)
                .filter(InnerSchema.name == OuterSchema.name)
                .filter(InnerSchema.publish_date != null())
                .filter(InnerSchema.retract_date == null())
                .order_by(InnerSchema.publish_date.desc())
                .limit(1)
                .correlate(OuterSchema)
                .as_scalar()
                .label('title'))
            .add_column(
                Session.query(
                    group_concat(to_date(InnerSchema.publish_date), ';'))
                .filter(InnerSchema.name == OuterSchema.name)
                .filter(InnerSchema.publish_date != null())
                .filter(InnerSchema.retract_date == null())
                .group_by(InnerSchema.name)
                .correlate(OuterSchema)
                .as_scalar()
                .label('versions'))
            .filter(OuterSchema.publish_date != null())
            .filter(OuterSchema.retract_date == null()))

        schemata_query = (
            schemata_query
            .group_by(OuterSchema.name)
            .from_self())

        return schemata_query

    @classmethod
    def list_all(cls, include_rand=True, include_private=True):
        """
        Lists all the schema plans
        """
        subquery = cls._query().subquery()
        query = Session.query(subquery)

        if not include_rand:
            query = query.filter(~subquery.c.has_rand)

        if not include_private:
            query = query.filter(~subquery.c.has_private)

        query = query.order_by(subquery.c.title)

        return [cls.from_sql(r) for r in query]

    def codebook(self):
        knowns = [
            row('id', self.name, types.NUMERIC,
                is_required=True, is_system=True),
            row('pid', self.name, types.STRING,
                is_required=True, is_system=True),
            row('site', self.name, types.STRING,
                is_required=True, is_system=True),
            row('enrollment', self.name, types.NUMERIC,
                is_collection=True, is_system=True),
            row('enrollment_ids', self.name, types.NUMERIC,
                is_collection=True, is_system=True),
            row('visit_cycles', self.name, types.STRING, is_collection=True,
                is_system=True)]

        if self.has_rand:
            knowns.extend([
                row('block_number', self.name, types.NUMERIC,
                    is_required=True, is_system=True),
                row('randid', self.name, types.STRING, is_required=True,
                    is_system=True),
                row('arm_name', self.name, types.STRING, is_required=True,
                    is_system=True)])

        knowns.extend([
            row('form', self.name, types.STRING,
                is_required=True, is_system=True),
            row('publish_date', self.name, types.STRING,
                is_required=True, is_system=True),
            row('state', self.name, types.STRING,
                is_required=True, is_system=True),
            row('visit_date', self.name, types.DATE, is_system=True),
            row('visit_id', self.name, types.NUMERIC, is_system=True),
            row('collect_date', self.name, types.DATE,
                is_required=True, is_system=True),
            row('is_null', self.name, types.BOOLEAN,
                is_required=True, is_system=True),
            row('create_date', self.name, types.DATE,
                is_required=True, is_system=True),
            row('create_user', self.name, types.STRING,
                is_required=True, is_system=True),
            row('modify_date', self.name, types.DATE,
                is_required=True, is_system=True),
            row('modify_user', self.name, types.STRING, is_required=True,
                is_system=True)])

        for column in knowns:
            yield column

        query = (
            Session.query(models.Attribute)
            .join(models.Schema)
            .filter(models.Schema.name == self.name)
            .filter(models.Schema.publish_date.in_(self.versions))
            .filter(models.Schema.retract_date == null()))

        query = (
            query.order_by(
                models.Attribute.name,
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
                      choices=[(c.name, c.title)
                               for c in itervalues(attribute.choices)])

    def data(self, use_choice_labels=False, expand_collections=False):
        """
        Generates a studies report containing the patient's metadata
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

        ids_query = (
            Session.query(models.Schema.id)
            .filter(models.Schema.publish_date.in_(self.versions)))
        ids = [id for id, in ids_query]

        report = build_report(
            Session,
            self.name,
            ids=ids,
            expand_collections=expand_collections,
            use_choice_labels=use_choice_labels)

        query = (
            Session.query(report.c.id.label('id'))
            .add_column(
                Session.query(models.Site.name)
                .select_from(models.Patient)
                .join(models.Site)
                .join(models.Context,
                      (models.Context.external == u'patient')
                      & (models.Context.key == models.Patient.id))
                .filter(models.Context.entity_id == report.c.id)
                .correlate(report)
                .as_scalar()
                .label('site'))
            .add_column(
                Session.query(models.Patient.pid)
                .join(models.Context,
                      (models.Context.external == u'patient')
                      & (models.Context.key == models.Patient.id))
                .filter(models.Context.entity_id == report.c.id)
                .correlate(report)
                .as_scalar()
                .label('pid'))
            .add_column(
                Session.query(group_concat(models.Study.name, ';'))
                .select_from(models.Enrollment)
                .join(models.Study)
                .join(models.Context,
                      (models.Context.external == u'enrollment')
                      & (models.Context.key == models.Enrollment.id))
                .filter(models.Context.entity_id == report.c.id)
                .group_by(models.Context.entity_id)
                .correlate(report)
                .as_scalar()
                .label('enrollment'))
            .add_column(
                Session.query(group_concat(models.Enrollment.id, ';'))
                .select_from(models.Enrollment)
                .join(models.Context,
                      (models.Context.external == u'enrollment')
                      & (models.Context.key == models.Enrollment.id))
                .filter(models.Context.entity_id == report.c.id)
                .group_by(models.Context.entity_id)
                .correlate(report)
                .as_scalar()
                .label('enrollment_ids'))
            .add_column(
                Session.query(models.Visit.id)
                .select_from(models.Visit)
                .join(models.Context,
                      (models.Context.external == u'visit')
                      & (models.Context.key == models.Visit.id))
                .filter(models.Context.entity_id == report.c.id)
                .correlate(report)
                .as_scalar()
                .label('visit_id'))
            .add_column(
                Session.query(models.Visit.visit_date)
                .select_from(models.Visit)
                .join(models.Context,
                      (models.Context.external == u'visit')
                      & (models.Context.key == models.Visit.id))
                .filter(models.Context.entity_id == report.c.id)
                .correlate(report)
                .as_scalar()
                .label('visit_date'))
            .add_column(
                Session.query(group_concat(models.Study.title
                                           + literal_column(u"'('")
                                           + cast(models.Cycle.week, String)
                                           + literal_column(u"')'"),
                                           literal_column(u"';'")))
                .select_from(models.Visit)
                .join(models.Visit.cycles)
                .join(models.Cycle.study)
                .join(models.Context,
                      (models.Context.external == u'visit')
                      & (models.Context.key == models.Visit.id))
                .filter(models.Context.entity_id == report.c.id)
                .group_by(models.Context.entity_id)
                .correlate(report)
                .as_scalar()
                .label('visit_cycles')))

        if self.has_rand:
            query = (
                query
                .add_column(
                    Session.query(models.Stratum.block_number)
                    .select_from(models.Stratum)
                    .join(models.Context,
                          (models.Context.external == u'stratum')
                          & (models.Context.key == models.Stratum.id))
                    .filter(models.Context.entity_id == report.c.id)
                    .correlate(report)
                    .as_scalar()
                    .label('block_number'))
                .add_column(
                    Session.query(models.Stratum.randid)
                    .select_from(models.Stratum)
                    .join(models.Context,
                          (models.Context.external == u'stratum')
                          & (models.Context.key == models.Stratum.id))
                    .filter(models.Context.entity_id == report.c.id)
                    .correlate(report)
                    .as_scalar()
                    .label('randid'))
                .add_column(
                    Session.query(models.Arm.title)
                    .select_from(models.Stratum)
                    .join(models.Context,
                          (models.Context.external == u'stratum')
                          & (models.Context.key == models.Stratum.id))
                    .filter(models.Context.entity_id == report.c.id)
                    .join(models.Stratum.arm)
                    .correlate(report)
                    .as_scalar()
                    .label('arm_name')))

        query = query.add_columns(
            *[c for c in report.columns if c.name != 'id'])

        return query
