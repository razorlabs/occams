"""
Auditing components for mappings.
Note that the majory of this code was copied from the SQLAlchemy examples on
``versioning``/``history``. Our team decided to rename the mechanics to
``auditing`` as we felt it was a better suited name and also avoids confusion
with the schema deep-copying mechanics we already have (which our team
refers to as ``versioning``)

Credit to **zzzeek** et al.
"""
from itertools import ifilter

from sqlalchemy import Column
from sqlalchemy import ForeignKeyConstraint
from sqlalchemy import Integer
from sqlalchemy import Table
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import mapper
from sqlalchemy.orm import attributes
from sqlalchemy.orm import object_mapper
from sqlalchemy.orm import object_session
from sqlalchemy.orm.exc import UnmappedColumnError
from sqlalchemy.orm.properties import RelationshipProperty


class Auditable(object):
    """
    Enables a mapping to have an "audit" table of previous modifications done
    to its entries. Useful for auditing purposes and helps keeping old entries
    backed up without interfering with "live" data.
    """

    @declared_attr
    def __mapper_cls__(cls):
        def map(cls, *arg, **kw):
            mp = mapper(cls, *arg, **kw)
            auditMapper(mp)
            return mp
        return map


def auditMapper(live_mapper):
    """
    Creates an identical mapper for auditing purposes
    This method should only be called when the 'live' table's mapper is complete
    so that it can properly replicate all the corresponding columns.
    """

    # Set the 'active_history' flag only on column-mapped attributes so that
    # the old revision of the info is always loaded
    for prop in live_mapper.iterate_properties:
        getattr(live_mapper.class_, prop.key).impl.active_history = True

    super_mapper = live_mapper.inherits
    super_history_mapper = getattr(live_mapper.class_, '__audit_mapper__', None)

    polymorphic_on = None

    # Work on inheritance
    if not super_mapper or live_mapper.local_table is not super_mapper.local_table:
        super_fks = []
        cols = []

        def col_references_table(col, table):
            for fk in col.foreign_keys:
                if fk.references(table):
                    return True
            return False

        for column in ifilter(lambda c: c.name != 'revision', live_mapper.local_table.c):

            col = column.copy()
            col.unique = False

            if super_mapper and col_references_table(column, super_mapper.local_table):
                super_fks.append((col.key, list(super_history_mapper.local_table.primary_key)[0]))

            cols.append(col)

            if column is live_mapper.polymorphic_on:
                polymorphic_on = col

        if super_mapper:
            super_fks.append(('revision', super_history_mapper.base_mapper.local_table.c.revision))
            cols.append(Column('revision', Integer, primary_key=True))
        else:
            cols.append(Column('revision', Integer, primary_key=True))

        if super_fks:
            cols.append(ForeignKeyConstraint(*zip(*super_fks)))

        table = Table(
            live_mapper.local_table.name + '_audit',
            live_mapper.local_table.metadata,
           *cols
           )
    else:
        # single table inheritance.  take any additional columns that may have
        # been added and add them to the history table.
        for column in live_mapper.local_table.c:
            if column.key not in super_history_mapper.local_table.c:
                col = column.copy()
                col.unique = False
                super_history_mapper.local_table.append_column(col)

        table = None

    if super_history_mapper:
        bases = (super_history_mapper.class_,)
    else:
        bases = live_mapper.base_mapper.class_.__bases__

    # Create the final audit mapper and attach it to the live mapper class
    # for convenient reference
    live_mapper.class_.__audit_mapper__ = mapper(
        class_=type.__new__(type, '%sAudit' % live_mapper.class_.__name__, bases, {}),
        local_table=table,
        inherits=super_history_mapper,
        polymorphic_on=polymorphic_on,
        polymorphic_identity=live_mapper.polymorphic_identity
        )

    if not super_history_mapper:
        revisionColumn = Column('revision', Integer, default=1, nullable=False)
        live_mapper.local_table.append_column(revisionColumn)
        live_mapper.add_property('revision', live_mapper.local_table.c.revision)


def createRevision(instance, deleted=False):
    """
    Inspects the instance for changes and bumps it's previous row data to
    the audit table.
    """

    liveMapper = object_mapper(instance)
    auditMapper = instance.__audit_mapper__
    instanceState = attributes.instance_state(instance)

    values = dict()
    changed = False

    for lm, am in zip(liveMapper.iterate_to_root(), auditMapper.iterate_to_root()):
        if not am.single:
            for auditColumn in ifilter(lambda c: c.key != 'revision', am.local_table.c):
                liveColumn = lm.local_table.c[auditColumn.key]

                # get the value of the attribute based on the MapperProperty
                # related to the mapped column.  this will allow usage of
                # MapperProperties that have a different keyname than that
                # of the mapped column.
                try:
                    liveProperty = liveMapper.get_property_by_column(liveColumn)
                except UnmappedColumnError:
                    # in the case of single table inheritance, there may be
                    # columns on the mapped table intended for the subclass
                    # only. the 'unmapped' status of the subclass column on
                    # the base class is a feature of the declarative module
                    # as of sqla 0.5.2.
                    continue

                # expired object attributes and also deferred cols might not
                # be in the dict.  force it to load no matter what by using
                # getattr().
                if liveProperty.key not in instanceState.dict:
                    getattr(instance, liveProperty.key)

                # (new value for live table / unchanged value / previous value)
                (new, unchanged, previous) = attributes.get_history(instance, liveProperty.key)

                if previous:
                    values[auditColumn.key] = previous[0]
                    changed = True
                elif unchanged:
                    values[auditColumn.key] = unchanged[0]
                else: # pragma: no cover
                    # Typically the first clause will catch changes from
                    # a previous value. There is no conceivable case where
                    # this exception might be thrown, but we added it
                    # for completeness as we do not want faulty values added.
                    # Previous code was:
                    #     values[auditColumn.key] = new[0]
                    #     changed = True
                    raise NotImplementedError(
                        'Received unexpected case where a instance was updated '
                        'with a value that it previously did not have or was '
                        'aware of.'
                        )

    if changed or deleted:
        # Commit previous values to audit table
        session = object_session(instance)
        values['revision'] = instance.revision
        audit_cls = auditMapper.class_
        session.add(audit_cls(**values))
        instance.revision += 1

