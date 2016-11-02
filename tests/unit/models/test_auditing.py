"""
Tests for auditing components.
Note that these tests were mostly (if not entirely) copied from the SQLAlchemy
examples for versioning.

Credits to **zzzeek** et al.
"""

import six

import sqlalchemy as sa
from sqlalchemy import exc as sa_exc
from sqlalchemy import event
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, deferred, relationship, scoped_session  # NOQA

from occams.models.auditing import Auditable, createRevision


def auditing_session(session):
    @event.listens_for(session, 'before_flush')
    def before_flush(session, flush_context, instances):
        auditable = lambda i: isinstance(i, Auditable)
        for obj in filter(auditable, session.dirty):
            createRevision(obj)
        for obj in filter(auditable, session.deleted):
            createRevision(obj, deleted=True)


def eq_(a, b, msg=None):  # pragma: no cover
    """Assert a == b, with repr messaging on failure."""
    assert a == b, msg or "%r != %r" % (a, b)


_repr_stack = set()


class BasicEntity(object):  # pragma: no cover
    def __init__(self, **kw):
        for key, value in six.iteritems(kw):
            setattr(self, key, value)

    def __repr__(self):
        if id(self) in _repr_stack:
            return object.__repr__(self)
        _repr_stack.add(id(self))
        try:
            return "%s(%s)" % (
                (self.__class__.__name__),
                ', '.join(["%s=%r" % (key, getattr(self, key))
                           for key in sorted(self.__dict__.keys())
                           if not key.startswith('_')]))
        finally:
            _repr_stack.remove(id(self))


_recursion_stack = set()


class ComparableEntity(BasicEntity):  # pragma: no cover
    def __hash__(self):
        return hash(self.__class__)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        """'Deep, sparse compare.

        Deeply compare two entities, following the non-None attributes of the
        non-persisted object, if possible.

        """
        if other is self:
            return True
        elif not self.__class__ == other.__class__:
            return False

        if id(self) in _recursion_stack:
            return True
        _recursion_stack.add(id(self))

        try:
            # pick the entity thats not SA persisted as the source
            try:
                self_key = sa.orm.attributes.instance_state(self).key
            except sa.orm.exc.NO_STATE:
                self_key = None

            if other is None:
                a = self
                b = other
            elif self_key is not None:
                a = other
                b = self
            else:
                a = self
                b = other

            for attr in a.__dict__.keys():
                if attr.startswith('_'):
                    continue
                value = getattr(a, attr)

                try:
                    # handle lazy loader errors
                    battr = getattr(b, attr)
                except (AttributeError, sa_exc.UnboundExecutionError):
                    return False

                if hasattr(value, '__iter__'):
                    if list(value) != list(battr):
                        return False
                else:
                    if value is not None and value != battr:
                        return False
            return True
        finally:
            _recursion_stack.remove(id(self))


def test_plain():
    Base = declarative_base(bind=create_engine('sqlite://'))

    class SomeClass(Auditable, Base, ComparableEntity):
        __tablename__ = 'sometable'

        id = Column(Integer, primary_key=True)
        name = Column(String(50))

    Base.metadata.create_all()
    session = scoped_session(sessionmaker())
    auditing_session(session)

    sc = SomeClass(name='sc1')
    session.add(sc)
    session.commit()

    sc.name = 'sc1modified'
    session.commit()

    assert sc.revision == 2

    SomeClassHistory = SomeClass.__audit_mapper__.class_

    eq_(
        session.query(SomeClassHistory)
        .filter(SomeClassHistory.revision == 1)
        .all(),
        [SomeClassHistory(revision=1, name='sc1')])

    sc.name = 'sc1modified2'

    eq_(
        session.query(SomeClassHistory)
        .order_by(SomeClassHistory.revision)
        .all(),
        [
            SomeClassHistory(revision=1, name='sc1'),
            SomeClassHistory(revision=2, name='sc1modified')])

    assert sc.revision == 3

    session.commit()

    sc.name = 'temp'
    sc.name = 'sc1modified2'

    session.commit()

    eq_(
        session.query(SomeClassHistory)
        .order_by(SomeClassHistory.revision)
        .all(),
        [
            SomeClassHistory(revision=1, name='sc1'),
            SomeClassHistory(revision=2, name='sc1modified')])

    session.delete(sc)
    session.commit()

    eq_(
        session.query(SomeClassHistory)
        .order_by(SomeClassHistory.revision)
        .all(),
        [
            SomeClassHistory(revision=1, name='sc1'),
            SomeClassHistory(revision=2, name='sc1modified'),
            SomeClassHistory(revision=3, name='sc1modified2')])


def test_from_null_with_flushes():
    Base = declarative_base(bind=create_engine('sqlite://'))

    class SomeClass(Auditable, Base, ComparableEntity):
        __tablename__ = 'sometable'

        id = Column(Integer, primary_key=True)
        name = Column(String(50))

    Base.metadata.create_all()
    session = scoped_session(sessionmaker())
    auditing_session(session)

    sc = SomeClass()
    session.add(sc)
    session.flush()

    sc.name = 'sc1'
    session.flush()

    assert sc.revision == 2


def test_from_null_with_commits():
    Base = declarative_base(bind=create_engine('sqlite://'))

    class SomeClass(Auditable, Base, ComparableEntity):
        __tablename__ = 'sometable'

        id = Column(Integer, primary_key=True)
        name = Column(String(50))

    Base.metadata.create_all()
    session = scoped_session(sessionmaker())
    auditing_session(session)

    sc = SomeClass()
    session.add(sc)
    session.commit()

    sc.name = 'sc1'
    session.commit()

    assert sc.revision == 2


def test_deferred():
    """test versioning of unloaded, deferred columns."""
    Base = declarative_base(bind=create_engine('sqlite://'))

    class SomeClass(Auditable, Base, ComparableEntity):
        __tablename__ = 'sometable'

        id = Column(Integer, primary_key=True)
        name = Column(String(50))
        data = deferred(Column(String(25)))

    Base.metadata.create_all()
    session = scoped_session(sessionmaker())
    auditing_session(session)

    sc = SomeClass(name='sc1', data='somedata')
    session.add(sc)
    session.commit()
    session.close()

    sc = session.query(SomeClass).first()
    assert 'data' not in sc.__dict__

    sc.name = 'sc1modified'
    session.commit()

    assert sc.revision == 2

    SomeClassHistory = SomeClass.__audit_mapper__.class_

    eq_(
        session.query(SomeClassHistory)
        .filter(SomeClassHistory.revision == 1)
        .all(),
        [SomeClassHistory(revision=1, name='sc1', data='somedata')])


def test_joined_inheritance():
    Base = declarative_base(bind=create_engine('sqlite://'))

    class BaseClass(Auditable, Base, ComparableEntity):
        __tablename__ = 'basetable'

        id = Column(Integer, primary_key=True)
        name = Column(String(50))
        type = Column(String(20))

        __mapper_args__ = {'polymorphic_on': type,
                           'polymorphic_identity': 'base'}

    class SubClassSeparatePk(BaseClass):
        __tablename__ = 'subtable1'

        id = Column(Integer, primary_key=True)
        base_id = Column(Integer, ForeignKey('basetable.id'))
        subdata1 = Column(String(50))

        __mapper_args__ = {'polymorphic_identity': 'sep'}

    class SubClassSamePk(BaseClass):
        __tablename__ = 'subtable2'

        id = Column(Integer, ForeignKey('basetable.id'), primary_key=True)
        subdata2 = Column(String(50))

        __mapper_args__ = {'polymorphic_identity': 'same'}

    Base.metadata.create_all()
    session = scoped_session(sessionmaker())
    auditing_session(session)

    sep1 = SubClassSeparatePk(name='sep1', subdata1='sep1subdata')
    base1 = BaseClass(name='base1')
    same1 = SubClassSamePk(name='same1', subdata2='same1subdata')
    session.add_all([sep1, base1, same1])
    session.commit()

    base1.name = 'base1mod'
    same1.subdata2 = 'same1subdatamod'
    sep1.name = 'sep1mod'
    session.commit()

    BaseClassHistory = BaseClass.__audit_mapper__.class_
    SubClassSeparatePkHistory = SubClassSeparatePk.__audit_mapper__.class_
    SubClassSamePkHistory = SubClassSamePk.__audit_mapper__.class_
    eq_(
        session.query(BaseClassHistory)
        .order_by(BaseClassHistory.id)
        .all(),
        [
            SubClassSeparatePkHistory(id=1, name=u'sep1', type=u'sep',
                                      revision=1),
            BaseClassHistory(id=2, name=u'base1', type=u'base',
                             revision=1),
            SubClassSamePkHistory(id=3, name=u'same1', type=u'same',
                                  revision=1)])

    same1.subdata2 = 'same1subdatamod2'

    eq_(
        session.query(BaseClassHistory)
        .order_by(BaseClassHistory.id, BaseClassHistory.revision)
        .all(),
        [
            SubClassSeparatePkHistory(id=1, name=u'sep1', type=u'sep',
                                      revision=1),
            BaseClassHistory(id=2, name=u'base1', type=u'base',
                             revision=1),
            SubClassSamePkHistory(id=3, name=u'same1', type=u'same',
                                  revision=1),
            SubClassSamePkHistory(id=3, name=u'same1', type=u'same',
                                  revision=2)])

    base1.name = 'base1mod2'
    eq_(
        session.query(BaseClassHistory)
        .order_by(BaseClassHistory.id, BaseClassHistory.revision)
        .all(),
        [
            SubClassSeparatePkHistory(id=1, name=u'sep1', type=u'sep',
                                      revision=1),
            BaseClassHistory(id=2, name=u'base1', type=u'base',
                             revision=1),
            BaseClassHistory(id=2, name=u'base1mod', type=u'base',
                             revision=2),
            SubClassSamePkHistory(id=3, name=u'same1', type=u'same',
                                  revision=1),
            SubClassSamePkHistory(id=3, name=u'same1', type=u'same',
                                  revision=2)])


def test_single_inheritance():
    Base = declarative_base(bind=create_engine('sqlite://'))

    class BaseClass(Auditable, Base, ComparableEntity):
        __tablename__ = 'basetable'

        id = Column(Integer, primary_key=True)
        name = Column(String(50))
        type = Column(String(50))
        __mapper_args__ = {'polymorphic_on': type,
                           'polymorphic_identity': 'base'}

    class SubClass(BaseClass):

        subname = Column(String(50), unique=True)
        __mapper_args__ = {'polymorphic_identity': 'sub'}

    Base.metadata.create_all()
    session = scoped_session(sessionmaker())
    auditing_session(session)

    b1 = BaseClass(name='b1')
    sc = SubClass(name='s1', subname='sc1')

    session.add_all([b1, sc])

    session.commit()

    b1.name = 'b1modified'

    BaseClassHistory = BaseClass.__audit_mapper__.class_
    SubClassHistory = SubClass.__audit_mapper__.class_

    eq_(
        session.query(BaseClassHistory)
        .order_by(BaseClassHistory.id, BaseClassHistory.revision)
        .all(),
        [BaseClassHistory(id=1, name=u'b1', type=u'base', revision=1)])

    sc.name = 's1modified'
    b1.name = 'b1modified2'

    eq_(
        session.query(BaseClassHistory)
        .order_by(BaseClassHistory.id, BaseClassHistory.revision)
        .all(),
        [
            BaseClassHistory(id=1, name=u'b1', type=u'base', revision=1),
            BaseClassHistory(id=1, name=u'b1modified', type=u'base',
                             revision=2),
            SubClassHistory(id=2, name=u's1', type=u'sub', revision=1)])

    # test the unique constraint on the subclass
    # column
    sc.name = "modifyagain"
    session.flush()


def test_unique():
    Base = declarative_base(bind=create_engine('sqlite://'))

    class SomeClass(Auditable, Base, ComparableEntity):
        __tablename__ = 'sometable'

        id = Column(Integer, primary_key=True)
        name = Column(String(50), unique=True)
        data = Column(String(50))

    Base.metadata.create_all()
    session = scoped_session(sessionmaker())
    auditing_session(session)

    sc = SomeClass(name='sc1', data='sc1')
    session.add(sc)
    session.commit()

    sc.data = 'sc1modified'
    session.commit()

    assert sc.revision == 2

    sc.data = 'sc1modified2'
    session.commit()

    assert sc.revision == 3
