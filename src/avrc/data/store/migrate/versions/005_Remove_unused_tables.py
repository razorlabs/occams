
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy.exc
from sqlalchemy import *
from migrate import *


Model = declarative_base()

# Where is curator?
# The table 'curator' is an artifact of an older model that was removed and
# never syncronized with the database. (This was before sqlalchemy-migrate
# was in use in this project)


# Where is binary?
# See curator explanation.

# Dropped: not being used in live system, and will be native in DS1
include_table = Table('include', Model.metadata,
    Column('main_id', ForeignKey('specification.id', ondelete='CASCADE')),
    Column('include_id', ForeignKey('specification.id', ondelete='CASCADE')),
    PrimaryKeyConstraint('main_id', 'include_id')
    )


# Dropped: currently not reasonable support available, possibly a DS2 feature
class Invariant(Model):
    __tablename__ = 'invariant'

    id = Column(Integer, primary_key=True)

    schema_id = Column(
        Integer,
        ForeignKey('schema.id', ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    name = Column(Unicode, nullable=False)


class Keyword(Model):
    __tablename__ = 'keyword'

    id = Column(Integer, primary_key=True)

    instance_id = Column(
        ForeignKey('instance.id', ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    title = Column(Unicode, nullable=False, index=True)

    is_synonym = Column(Boolean, nullable=False, default=True)


def upgrade(migrate_engine):
    """ Removes tables that have not been used since launch and have no
        foreseeable use in the future.
    """
    metadata = MetaData(bind=migrate_engine)

    for table_name in (u'curator', u'binary', u'invariant', u'include', 'keyword'):
        try:
            Table(table_name, metadata, autoload=True).drop()
        except sqlalchemy.exc.NoSuchTableError as e:
            if table_name not in  (u'curator', u'binary'):
                raise e


def downgrade(migrate_engine):
    metadata = MetaData(migrate_engine)
    metadata.reflect(only=['specification', 'schema', 'instance'])

    Invariant.__table__.tometadata(metadata).create()
    include_table.tometadata(metadata).create()
    Keyword.__table.tometadata(metadata).create()


