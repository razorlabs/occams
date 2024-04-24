"""
Common metadata modules
"""

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declared_attr

from .meta import Base


@sa.event.listens_for(Base.metadata, 'before_create')
def create_touch_procedures(target, connection, **kw):
    """
    Creates necessary stored procedures for updating record timestamps
    """

    connection.execute(r"""
        CREATE OR REPLACE FUNCTION touch() RETURNS TRIGGER AS $$
        DECLARE
            _user_id int;
            _user text;
            _timestamp timestamp;
        BEGIN
            _timestamp := timeofday();
            _user := (SELECT lower(current_setting('application.user')));

            SELECT id FROM account WHERE key = _user INTO _user_id;

            IF NOT FOUND THEN
                INSERT INTO account (key) VALUES (_user) RETURNING id INTO _user_id;
            END IF;

            IF tg_op = 'INSERT' THEN
                NEW.create_user_id := _user_id;
                NEW.create_date := _timestamp;
            END IF;

            NEW.modify_user_id := _user_id;
            NEW.modify_date := _timestamp;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    connection.execute(r"""
        CREATE OR REPLACE FUNCTION touch_table(target_table regclass)
            RETURNS void AS $$
        BEGIN
            EXECUTE '
                DROP TRIGGER IF EXISTS touch_trigger ON ' || target_table || ';
                CREATE TRIGGER touch_trigger
                BEFORE INSERT OR UPDATE
                ON ' || target_table || '
                FOR EACH ROW EXECUTE PROCEDURE touch()';
        END;
        $$ LANGUAGE plpgsql;
    """)


class Referenceable(object):
    """
    Adds primary key id columns to tables.
    """

    id = sa.Column(
        sa.BigInteger,
        primary_key=True,
        doc='This value is auto-generated by the database and assigned to '
            'the item. It should not be modified, otherwise risking '
            'altered database behavior.')


class Describeable(object):
    """
    Adds standard content properties to tables.
    """

    name = sa.Column(
        sa.String,
        nullable=False,
        doc='This value is usually an ASCII label to be used for '
            'easy reference of the item. When naming an item, lowercase '
            'alphanumeric characters or hyphens. The name should also be '
            'unique within a container.')

    title = sa.Column(
        sa.Unicode,
        nullable=False,
        doc='Human readable name')

    description = sa.Column(sa.UnicodeText)


class User(Base, Referenceable):
    """
    A simple 'blame' user for audit trails
    """

    __tablename__ = 'account'

    key = sa.Column(
        sa.String,
        nullable=False,
        doc='A unique way of distinguishing a user (e.g. email or uid)')

    create_date = sa.Column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text('CURRENT_TIMESTAMP'))

    modify_date = sa.Column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text('CURRENT_TIMESTAMP'),
        onupdate=sa.text('CURRENT_TIMESTAMP'))

    @declared_attr
    def __table_args__(cls):
        return (
            sa.UniqueConstraint('key', name='uq_%s_key' % cls.__tablename__),
            sa.CheckConstraint(
                'create_date <= modify_date',
                name='ck_%s_valid_timeline' % cls.__tablename__))


class Modifiable(object):
    """
    Adds user edit modification meta data for lifecycle tracking.
    """

    @declared_attr
    def create_date(cls):
        return sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    @declared_attr
    def create_user_id(cls):
        return sa.Column(
            sa.Integer,
            sa.ForeignKey(
                User.id,
                name='fk_%s_create_user_id' % cls.__tablename__,
                ondelete='RESTRICT'
            ),
            nullable=False,
            index=True
        )

    @declared_attr
    def create_user(cls):
        return orm.relationship(User, foreign_keys=lambda: cls.create_user_id)

    @declared_attr
    def modify_date(cls):
        return sa.Column(
            sa.DateTime,
            sa.CheckConstraint(
                'create_date <= modify_date',
                'ck_%s_valid_timeline' % cls.__tablename__),
            nullable=False,
            default=datetime.now
        )

    @declared_attr
    def modify_user_id(cls):
        return sa.Column(
            sa.Integer,
            sa.ForeignKey(
                User.id,
                name='fk_%s_modify_user_id' % cls.__tablename__,
                ondelete='RESTRICT'),
            nullable=False,
            index=True
        )

    @declared_attr
    def modify_user(cls):
        return orm.relationship(User, foreign_keys=lambda: cls.modify_user_id)

    @classmethod
    def __declare_first__(cls):
        sa.event.listen(
            cls.__table__,
            'after_create',
            sa.DDL(r"select touch_table('%(fullname)s')")
        )