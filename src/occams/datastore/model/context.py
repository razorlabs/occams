
from sqlalchemy.types import Integer
from sqlalchemy.schema import Column
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.schema import ForeignKeyConstraint
from sqlalchemy.orm import relationship as Relationship
from sqlalchemy.ext.declarative import declared_attr

from occams.datastore.model import Model
from occams.datastore.model.metadata import AutoNamed
from occams.datastore.model.metadata import Referenceable
from occams.datastore.model.metadata import Describeable
from occams.datastore.model.metadata import Modifiable
from occams.datastore.model.metadata import buildModifiableConstraints
from occams.datastore.model.auditing import Auditable


class Context(Model, AutoNamed, Referenceable, Modifiable, Auditable):

    entity_id = Column(Integer, nullable=False)

    entity = Relationship('Entity')

    external_id = Column(Integer, nullable=False)

    external = Relationship('External')

    key = Column(Integer, nullable=False)

    @declared_attr
    def __table_args__(cls):
        return buildModifiableConstraints(cls) + (
            ForeignKeyConstraint(
                columns=['entity_id'],
                refcolumns=['entity.id'],
                name='fk_%s_entity_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),
            ForeignKeyConstraint(
                columns=['external_id'],
                refcolumns=['external.id'],
                name='fk_%s_external_id' % cls.__tablename__,
                ondelete='CASCADE',
                ),
            UniqueConstraint(
                'entity_id', 'external_id', 'key',
                name='uq_%s' % cls.__tablename__
                ),
            )


class External(Model, AutoNamed, Referenceable, Describeable, Modifiable, Auditable):

    @declared_attr
    def __table_args__(cls):
        return buildModifiableConstraints(cls) + (
            UniqueConstraint('name', name='uq_%s_name' % cls.__tablename__),
            )
