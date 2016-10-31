"""
Storage models
"""

from datetime import date

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm.collections import attribute_mapped_collection

from .metadata import Referenceable, Describeable, Modifiable
from .meta import Base
from .schema import Schema


class Context(Base, Referenceable, Modifiable):

    __tablename__ = 'context'

    entity_id = sa.Column(sa.Integer, nullable=False)

    # Discriminator column for the keys and associations
    external = sa.Column(sa.String, nullable=False)

    key = sa.Column(sa.Integer, nullable=False)

    @declared_attr
    def __table_args__(cls):
        return (
            sa.ForeignKeyConstraint(
                columns=['entity_id'],
                refcolumns=['entity.id'],
                name='fk_%s_entity_id' % cls.__tablename__,
                ondelete='CASCADE'),
            sa.UniqueConstraint('entity_id', 'external', 'key'),
            sa.Index(
                'ix_%s_external_key' % cls.__tablename__, 'external', 'key'))


class State(Base, Referenceable, Describeable, Modifiable):
    """
    An entity state to keep track of the entity's progress through some
    externally defined work flow.
    """

    __tablename__ = 'state'

    @declared_attr
    def __table_args__(cls):
        return (sa.UniqueConstraint('name'),)

    @classmethod
    def __declare_last__(cls):
        """
        Override modifiable's declare last to add additional content
        """
        def populate_default_states(target, connection, **kw):
            """
            We currently only ship with hard-coded states.
            """

            connection.execute(target.insert().values([
                dict(name=u'pending-entry', title=u'Pending Entry'),
                dict(name=u'in-progress', title=u'In Progress'),
                dict(name=u'pending-review', title=u'Pending Review'),
                dict(name=u'pending-correction', title=u'Pending Correction'),
                dict(name=u'complete', title=u'Complete'),
            ]))

        sa.event.listen(
            cls.__table__,
            'after_create',
            sa.DDL(r"select touch_table('%(fullname)s')")
        )

        sa.event.listen(cls.__table__, 'after_create', populate_default_states)


class Entity(Base, Referenceable, Modifiable):
    """
    An object that describes how an EAV object is generated.
    """

    __tablename__ = 'entity'

    schema_id = sa.Column(sa.Integer, nullable=False)

    schema = orm.relationship(
        Schema,
        doc='The scheme the object will provide once generated.')

    contexts = orm.relationship(
        Context,
        cascade='all, delete-orphan',
        backref=orm.backref(
            name='entity'))

    state_id = sa.Column(sa.Integer)

    state = orm.relationship(
        State,
        backref=orm.backref(
            name='entities',
            lazy='dynamic'),
        doc='The current workflow state')

    not_done = sa.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.text('FALSE'),
        doc='Flag to indicate if the entity is intentionally blank')

    collect_date = sa.Column(
        sa.Date,
        nullable=False,
        default=date.today,
        doc='The date that the information was physically collected')

    data = sa.Column(JSONB)

    @declared_attr
    def __table_args__(cls):
        return (
            sa.ForeignKeyConstraint(
                columns=['schema_id'],
                refcolumns=['schema.id'],
                name='fk_%s_schema_id' % cls.__tablename__,
                ondelete='CASCADE'),
            sa.ForeignKeyConstraint(
                columns=['state_id'],
                refcolumns=['state.id'],
                name='fk_%s_state_id' % cls.__tablename__,
                ondelete='CASCADE'),
            sa.Index('ix_%s_schema_id' % cls.__tablename__, 'schema_id'),
            sa.Index('ix_%s_state_id' % cls.__tablename__, 'state_id'),
            sa.Index('ix_%s_collect_date' % cls.__tablename__, 'collect_date'))


class HasEntities(object):
    """
    Mixin class to allow other models to associate with entities using a
    central association class (i.e. ``Context``)
    """

    @declared_attr
    def contexts(cls):
        """
        Relationship to the context mapping class.
        If you want to be forwared to entities, use ``entities`` instead.
        """
        name = cls.__tablename__

        cls.entities = association_proxy(
            'contexts', 'entity',
            creator=lambda e: Context(entity=e, external=name))

        return orm.relationship(
            Context,
            primaryjoin=(
                '(%s.id == Context.key) & (Context.external == "%s")'
                % (cls.__name__, name)),
            foreign_keys=[Context.key, Context.external],
            collection_class=set,
            backref=orm.backref(
                '%s_parent' % name,
                uselist=False))


class EntityAttachment(Base, Referenceable, Modifiable):

    __tablename__ = 'entity_attachment'

    entity_id = sa.Column(
        sa.ForeignKey(Entity.id, ondelete='CASCADE'),
        nullable=False
    )

    entity = orm.relationship(
        Entity,
        backref=orm.backref(
            name='attachments',
            collection_class=attribute_mapped_collection('id'),
        )
    )

    file_name = sa.Column(
        sa.Unicode,
        nullable=False,
        doc='The original file name (we use a sanitized file name internally)'
    )

    mime_type = sa.Column(
        sa.String,
        nullable=False,
        doc='The MIME type of the file'
    )

    blob_id = sa.Column(
        sa.ForeignKey('entity_attachment_blob.id', ondelete='CASCADE'),
        nullable=False,
    )

    blob = orm.relationship('EntityAttachmentBlob')


class EntityAttachmentBlob(Base, Referenceable, Modifiable):

    __tablename__ = 'entity_attachment_blob'

    content = sa.Column(
        sa.LargeBinary,
        nullable=False,
        info={'audit_exclude': True}
    )
