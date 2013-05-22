import datetime

import colander
import deform
import deform.widget
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import view_config
from pyramid_deform import CSRFSchema
from sqlalchemy import func, orm

from occams.datastore import model as datastore

from .. import _, Session, Logger


@view_config(
    route_name='home',
    renderer='occams.form:/templates/form/list.pt',
    layout='master_layout')
def list_(request):
    """ Lists all forms used by instance.
    """
    layout = request.layout_manager.layout
    layout.content_title = _(u'Forms')
    query = query_names(Session)
    return {
        'forms': iter(query),
        'forms_count': query.count()}


@view_config(
    route_name='form_view',
    renderer='occams.form/templates/form/view.pt',
    layout='master_layout')
def view(request):
    """ Displays information about the current publication of the form
    """
    return {}


def query_names(session):
    """ Generates an iterable summary of the form names in the system
    """
    SummarySchema = orm.aliased(datastore.Schema, name='_summary_schema')
    query = (
        session.query(SummarySchema.name)
        .distinct()
        .add_column(
            session.query(datastore.Schema.title)
            .filter(datastore.Schema.name == SummarySchema.name)
            .order_by(
                (datastore.Schema.publish_date != None).desc(),
                datastore.Schema.publish_date.desc())
            .limit(1)
            .correlate(SummarySchema)
            .as_scalar()
            .label('title'))
        .add_column(
            session.query(func.min(datastore.Schema.publish_date))
            .filter(datastore.Schema.name == SummarySchema.name)
            .correlate(SummarySchema)
            .as_scalar()
            .label('start_date'))
        .add_column(
            session.query(func.max(datastore.Schema.publish_date))
            .filter(datastore.Schema.name == SummarySchema.name)
            .correlate(SummarySchema)
            .as_scalar()
            .label('publish_date'))
        .add_column(
            session.query(func.count())
            .filter(datastore.Schema.name == SummarySchema.name)
            .filter(datastore.Schema.publish_date != None)
            .correlate(SummarySchema)
            .as_scalar()
            .label('version_count'))
        .filter(~SummarySchema.is_inline)
        .order_by(SummarySchema.title.asc()))
    return query


def query_summary(session):
    """ Generates an iterable summary listing of forms in the system
    """
    SummarySchema = orm.aliased(datastore.Schema, name='_summary_schema')
    CreateUser = orm.aliased(datastore.User, name='_create_user')
    ModifyUser = orm.aliased(datastore.User, name='_modify_user')
    SubSchema = orm.aliased(datastore.Schema, name='_sub_schema')
    SubAttribute = orm.aliased(datastore.Attribute, name='_sub_attribute')
    query = (
        session.query(
            SummarySchema.id.label('id'),
            SummarySchema.name.label('name'),
            SummarySchema.title.label('title'),
            SummarySchema.revision.label('revision'),
            SummarySchema.state.label('state'),
            SummarySchema.publish_date.label('publish_date'),
            SummarySchema.create_date.label('create_date'),
            CreateUser.key.label('create_user'),
            SummarySchema.modify_date.label('modify_date'),
            ModifyUser.key.label('modify_user'))
        .add_column(
            session.query(func.count())
            .select_from(datastore.Schema)
            .outerjoin(datastore.Attribute,
                datastore.Attribute.schema_id == datastore.Schema.id)
            .outerjoin(SubSchema,
                SubSchema.id == datastore.Attribute.object_schema_id)
            .outerjoin(SubAttribute, SubAttribute.schema_id == SubSchema.id)
            .filter(datastore.Schema.id == SummarySchema.id)
            .correlate(SummarySchema)
            .as_scalar()
            .label('field_count'))
        .add_column((SummarySchema.publish_date == (
            session.query(func.max(datastore.Schema.publish_date))
            .filter(datastore.Schema.state == 'published')
            .filter(datastore.Schema.publish_date < datastore.NOW)
            .filter(datastore.Schema.name == SummarySchema.name)
            .correlate(SummarySchema)
            .as_scalar())).label('is_current'))
        .join(CreateUser, SummarySchema.create_user_id == CreateUser.id)
        .join(ModifyUser, SummarySchema.modify_user_id == ModifyUser.id)
        .filter(~SummarySchema.is_inline)
        .order_by(
            SummarySchema.title.asc(),
            (SummarySchema.publish_date != None).desc(),
            SummarySchema.publish_date.desc()))
    return query

