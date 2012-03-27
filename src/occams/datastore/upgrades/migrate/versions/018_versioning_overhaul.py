from sqlalchemy import *
from migrate import *


NOW = text('CURRENT_TIMESTAMP')


def upgrade(migrate_engine):
    pass


def downgrade(migrate_engine):
    """
    Not backwards compatible, u mad bro?
    """
