import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.hybrid import hybrid_property

from .meta import Base


START_ID = int('222222', base=36)


class Site(Base):
    """
    An originating site (e.g. organization, institution, etc) for OUR numbers
    """

    __tablename__ = 'rostersite'

    id = sa.Column(sa.Integer, primary_key=True)

    title = sa.Column(
        sa.Unicode,
        nullable=False,
        unique=True,
        doc='The name of the site, for our records')

    create_date = sa.Column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=sa.text('CURRENT_TIMESTAMP'))

    modify_date = sa.Column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=sa.text('CURRENT_TIMESTAMP'),
        onupdate=sa.text('CURRENT_TIMESTAMP'))


class Identifier(Base):
    """
    A registered OUR number
    """

    __tablename__ = 'identifier'

    id = sa.Column(
        sa.Integer,
        # lowest possible OUR number that satisfies bureaucratic requirements
        sa.Sequence('identifier_id_pk_seq', start=START_ID),
        primary_key=True)

    origin_id = sa.Column(
        sa.Integer,
        sa.ForeignKey(Site.id),
        nullable=False)

    origin = orm.relationship(
        Site,
        backref=orm.backref(
            name='identifiers',
            lazy='dynamic'),
        doc='The site that generated the OUR number')

    @hybrid_property
    def our_number(self):
        ALPHABET = '0123456789abcdefghijklmnopqrstuvwxyz'
        number = self.id
        # save the sign for later
        sign = '' if int(number) >= 0 else '-'
        number = abs(int(number))
        base36 = '' if number > 0 else '0'

        # keep dividing until zero, using the mod as the character position
        while number != 0:
            number, mod = divmod(number, len(ALPHABET))
            base36 = ALPHABET[mod] + base36

        encoded = (sign + base36).rjust(6, '0')
        formatted = '%c%c%c-%c%c%c' % tuple(encoded)
        return formatted

    is_active = sa.Column(
        sa.Boolean,
        nullable=False,
        default=True,
        doc='Set to True if the OUR number is in circulation')

    create_date = sa.Column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=sa.text('CURRENT_TIMESTAMP'))

    modify_date = sa.Column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=sa.text('CURRENT_TIMESTAMP'),
        onupdate=sa.text('CURRENT_TIMESTAMP'))

    __table_args__ = dict(sqlite_autoincrement=True)

sa.event.listen(
    Identifier.__table__,
    'after_create',  # only do this when the table is created
    sa.DDL(
        'ALTER SEQUENCE identifier_id_pk_seq RESTART WITH %d'
        % START_ID
        ).execute_if(dialect=['postgresql', 'postgres']))
