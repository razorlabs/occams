from sqlalchemy import *
from migrate import *

CONSTRAINT_SQL = """
CASE
    WHEN type = 'object' THEN 
        object_schema_id IS NOT NULL AND is_inline_object IS NOT NULL
    ELSE 
        object_schema_id IS NULL AND is_inline_object IS NULL
END
"""

CONSTRAINT_NAME = 'attribute_valid_object_bind'

def upgrade(migrate_engine):
    """ Adds constraints to ensure that attributes which are objects specify
        a schema and inline flag
    """
    metadata = MetaData(migrate_engine)
    attribute_table = Table('attribute', metadata, autoload=True)

    constraint = CheckConstraint(
        CONSTRAINT_SQL,
        name=CONSTRAINT_NAME,
        table=attribute_table
        )

    constraint.create()


def downgrade(migrate_engine):
    metadata = MetaData(migrate_engine)
    attribute_table = Table('attribute', metadata, autoload=True)

    constraint = CheckConstraint(
        CONSTRAINT_SQL,
        name=CONSTRAINT_NAME,
        table=attribute_table
        )

    constraint.drop()
