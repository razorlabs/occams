import sqlalchemy as sa
from sqlalchemy.sql.elements import quoted_name
from sqlalchemy.ext.declarative import declarative_base

# Recommended naming convention used by Alembic, as various different database
# providers will autogenerate vastly different names making migrations more
# difficult. See: http://alembic.zzzcomputing.com/en/latest/naming.html
NAMING_CONVENTION = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = sa.MetaData(naming_convention=NAMING_CONVENTION)
Base = declarative_base(metadata=metadata)


@sa.event.listens_for(metadata, 'after_create')
def after_create(target, connection, **kw):
    for table in target.sorted_tables:

        if table.info.get('audit_exclude'):
            return

        exclude_columns = \
            [c.name for c in table.c if c.info.get('audit_exclude')]

        # Don't include query if certain rows are ignored from audit
        audit_query = 'f' if exclude_columns else 't'

        connection.execute(
            "SELECT audit.audit_table('%s', 'true', '%s', '{%s}'::text[])"
            % (table.name, audit_query, ','.join(exclude_columns))
        )
