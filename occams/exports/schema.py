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

from occams_datastore import models as datastore
from occams_datastore.reporting import build_report
from occams_datastore.utils.sql import group_concat, to_date

from .. import models
from .plan import ExportPlan
from .codebook import types, row


class SchemaPlan(ExportPlan):

    is_system = False

    @classmethod
    def from_sql(cls, db_session, record):
        """
        Creates a plan instance from an internal query inspection
        """
        report = cls(db_session)
        report.name = record.name
        report.title = record.title
        report.has_private = record.has_private
        report.has_rand = record.has_rand
        report.versions = sorted([datetime.strptime(v, '%Y-%m-%d').date()
                                  for v in record.versions.split(';')])
        return report

    @classmethod
    def from_schema(cls, db_session, name):
        """
        Creates a plan from a schema name
        """
        subquery = _list_schemata_info(db_session).subquery()
        query = db_session.query(subquery).filter(subquery.c.name == name)
        return cls.from_sql(db_session, query.one())

    @classmethod
    def list_all(cls, db_session, include_rand=True, include_private=True):
        """
        Lists all the schema plans
        """
        subquery = _list_schemata_info(db_session).subquery()
        query = db_session.query(subquery)

        if not include_rand:
            query = query.filter(~subquery.c.has_rand)

        if not include_private:
            query = query.filter(~subquery.c.has_private)

        query = query.order_by(subquery.c.title)

        return [cls.from_sql(db_session, r) for r in query]

    @property
    def _is_aeh_partner_form(self):
        return (
            'aeh' in self.db_session.bind.url.database
            and self.name in (
                'IPartnerBio',
                'IPartnerContact',
                'IPartnerDemographics',
                'IPartnerDisclosure'))

    def codebook(self):
        session = self.db_session
        knowns = [
            row('id', self.name, types.NUMBER, decimal_places=0,
                is_required=True, is_system=True),
            row('pid', self.name, types.STRING,
                is_required=True, is_system=True),
            row('site', self.name, types.STRING,
                is_required=True, is_system=True),
            row('enrollment', self.name, types.NUMBER, decimal_places=0,
                is_collection=True, is_system=True),
            row('enrollment_ids', self.name, types.NUMBER, decimal_places=0,
                is_collection=True, is_system=True)]

        if self._is_aeh_partner_form:
            knowns.extend([
                row('partner_id', self.name, types.NUMBER, decimal_places=0,
                    is_required=True, is_system=True,
                    desc=u'The partner linkage ID this form was collected for.'),
                row('parter_pid', self.name, types.STRING, is_system=True,
                    desc=u'The partner linkage PID this form was collected for. '
                         u'Available only if the partner is actually enrolled.')])

        if self.has_rand:
            knowns.extend([
                row('block_number', self.name, types.NUMBER, decimal_places=0,
                    is_required=True, is_system=True),
                row('randid', self.name, types.STRING, is_required=True,
                    is_system=True),
                row('arm_name', self.name, types.STRING, is_required=True,
                    is_system=True)])

        knowns.extend([
            row('visit_cycles', self.name, types.STRING, is_collection=True,
                is_system=True),
            row('visit_date', self.name, types.DATE, is_system=True),
            row('visit_id', self.name, types.NUMBER, decimal_places=0, is_system=True),
            row('form_name', self.name, types.STRING,
                is_required=True, is_system=True),
            row('form_publish_date', self.name, types.STRING,
                is_required=True, is_system=True),
            row('state', self.name, types.STRING,
                is_required=True, is_system=True),
            row('collect_date', self.name, types.DATE,
                is_required=True, is_system=True),
            row('not_done', self.name, types.BOOLEAN,
                is_required=True, is_system=True)])

        for column in knowns:
            yield column

        query = (
            session.query(datastore.Attribute)
            .join(datastore.Schema)
            .filter(datastore.Schema.name == self.name)
            .filter(datastore.Schema.publish_date.in_(self.versions))
            .filter(datastore.Schema.retract_date == null()))

        query = (
            query.order_by(
                datastore.Attribute.name,
                datastore.Schema.publish_date))

        for attribute in query:
            yield row(attribute.name, attribute.schema.name, attribute.type,
                      decimal_places=attribute.decimal_places,
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

        footer = [
            row('create_date', self.name, types.DATE,
                is_required=True, is_system=True),
            row('create_user', self.name, types.STRING,
                is_required=True, is_system=True),
            row('modify_date', self.name, types.DATE,
                is_required=True, is_system=True),
            row('modify_user', self.name, types.STRING, is_required=True,
                is_system=True)]

        for column in footer:
            yield column

    def data(self,
             use_choice_labels=False,
             expand_collections=False,
             ignore_private=True):
        session = self.db_session
        ids_query = (
            session.query(datastore.Schema.id)
            .filter(datastore.Schema.publish_date.in_(self.versions)))
        ids = [id for id, in ids_query]

        report = build_report(
            session,
            self.name,
            ids=ids,
            expand_collections=expand_collections,
            use_choice_labels=use_choice_labels,
            ignore_private=ignore_private)

        query = (
            session.query(report.c.id.label('id'))
            .add_column(
                session.query(models.Patient.pid)
                .join(datastore.Context,
                      (datastore.Context.external == u'patient')
                      & (datastore.Context.key == models.Patient.id))
                .filter(datastore.Context.entity_id == report.c.id)
                .correlate(report)
                .as_scalar()
                .label('pid'))
            .add_column(
                session.query(models.Site.name)
                .select_from(models.Patient)
                .join(models.Site)
                .join(datastore.Context,
                      (datastore.Context.external == u'patient')
                      & (datastore.Context.key == models.Patient.id))
                .filter(datastore.Context.entity_id == report.c.id)
                .correlate(report)
                .as_scalar()
                .label('site'))
            .add_column(
                session.query(group_concat(models.Study.name, ';'))
                .select_from(models.Enrollment)
                .join(models.Study)
                .join(datastore.Context,
                      (datastore.Context.external == u'enrollment')
                      & (datastore.Context.key == models.Enrollment.id))
                .filter(datastore.Context.entity_id == report.c.id)
                .group_by(datastore.Context.entity_id)
                .correlate(report)
                .as_scalar()
                .label('enrollment'))
            .add_column(
                session.query(group_concat(models.Enrollment.id, ';'))
                .select_from(models.Enrollment)
                .join(datastore.Context,
                      (datastore.Context.external == u'enrollment')
                      & (datastore.Context.key == models.Enrollment.id))
                .filter(datastore.Context.entity_id == report.c.id)
                .group_by(datastore.Context.entity_id)
                .correlate(report)
                .as_scalar()
                .label('enrollment_ids'))
            )

        if self._is_aeh_partner_form:
            PartnerPatient = orm.aliased(models.Patient)
            query = (
                query
                .add_column(
                    session.query(models.Partner.id)
                    .select_from(models.Partner)
                    .join(datastore.Context,
                          (datastore.Context.external == u'partner')
                          & (datastore.Context.key == models.Partner.id))
                    .filter(datastore.Context.entity_id == report.c.id)
                    .correlate(report)
                    .as_scalar()
                    .label('partner_id'))
                .add_column(
                    session.query(PartnerPatient.pid)
                    .select_from(models.Partner)
                    .join(PartnerPatient, models.Partner.enrolled_patient)
                    .join(datastore.Context,
                          (datastore.Context.external == u'partner')
                          & (datastore.Context.key == models.Partner.id))
                    .filter(datastore.Context.entity_id == report.c.id)
                    .correlate(report)
                    .as_scalar()
                    .label('partner_pid')))

        if self.has_rand:
            query = (
                query
                .add_column(
                    session.query(models.Stratum.block_number)
                    .select_from(models.Stratum)
                    .join(datastore.Context,
                          (datastore.Context.external == u'stratum')
                          & (datastore.Context.key == models.Stratum.id))
                    .filter(datastore.Context.entity_id == report.c.id)
                    .correlate(report)
                    .as_scalar()
                    .label('block_number'))
                .add_column(
                    session.query(models.Stratum.randid)
                    .select_from(models.Stratum)
                    .join(datastore.Context,
                          (datastore.Context.external == u'stratum')
                          & (datastore.Context.key == models.Stratum.id))
                    .filter(datastore.Context.entity_id == report.c.id)
                    .correlate(report)
                    .as_scalar()
                    .label('randid'))
                .add_column(
                    session.query(models.Arm.title)
                    .select_from(models.Stratum)
                    .join(datastore.Context,
                          (datastore.Context.external == u'stratum')
                          & (datastore.Context.key == models.Stratum.id))
                    .filter(datastore.Context.entity_id == report.c.id)
                    .join(models.Stratum.arm)
                    .correlate(report)
                    .as_scalar()
                    .label('arm_name')))

        query = (
            query
            .add_column(
                session.query(group_concat(models.Study.title
                                           + literal_column(u"'('")
                                           + cast(models.Cycle.week, String)
                                           + literal_column(u"')'"),
                                           literal_column(u"';'")))
                .select_from(models.Visit)
                .join(models.Visit.cycles)
                .join(models.Cycle.study)
                .join(datastore.Context,
                      (datastore.Context.external == u'visit')
                      & (datastore.Context.key == models.Visit.id))
                .filter(datastore.Context.entity_id == report.c.id)
                .group_by(datastore.Context.entity_id)
                .correlate(report)
                .as_scalar()
                .label('visit_cycles'))
            .add_column(
                session.query(models.Visit.id)
                .select_from(models.Visit)
                .join(datastore.Context,
                      (datastore.Context.external == u'visit')
                      & (datastore.Context.key == models.Visit.id))
                .filter(datastore.Context.entity_id == report.c.id)
                .correlate(report)
                .as_scalar()
                .label('visit_id'))
            .add_column(
                session.query(models.Visit.visit_date)
                .select_from(models.Visit)
                .join(datastore.Context,
                      (datastore.Context.external == u'visit')
                      & (datastore.Context.key == models.Visit.id))
                .filter(datastore.Context.entity_id == report.c.id)
                .correlate(report)
                .as_scalar()
                .label('visit_date'))
        )

        query = query.add_columns(
            *[c for c in report.columns if c.name != 'id'])

        return query


def _list_schemata_info(db_session):
    InnerSchema = orm.aliased(datastore.Schema)
    OuterSchema = orm.aliased(datastore.Schema)

    schemata_query = (
        db_session.query(OuterSchema.name.label('name'))
        .add_column(literal_column("'schema'").label('type'))
        .add_column(
            db_session.query(datastore.Attribute)
            .filter(datastore.Attribute.is_private)
            .join(InnerSchema)
            .filter(InnerSchema.name == OuterSchema.name)
            .correlate(OuterSchema)
            .exists()
            .label('has_private'))
        .add_column(
            db_session.query(datastore.Entity)
            .join(datastore.Entity.contexts)
            .filter(datastore.Context.external == 'stratum')
            .join(models.Stratum, datastore.Context.key == models.Stratum.id)
            .join(InnerSchema, datastore.Entity.schema)
            .filter(InnerSchema.name == OuterSchema.name)
            .correlate(OuterSchema)
            .exists()
            .label('has_rand'))
        .add_column(
            db_session.query(InnerSchema.title)
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
            db_session.query(
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
