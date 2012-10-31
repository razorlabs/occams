from AccessControl import getSecurityManager
import sqlalchemy as sa
from sqlalchemy import orm
from z3c import saconfig
from z3c.saconfig import interfaces as sa_interfaces
from zope import component
from zope import interface
from zope import component

from occams.datastore.model.session import DataStoreSession
from occams.datastore import model

from occams.form import interfaces


class EventAwareScopedSession(saconfig.GloballyScopedSession):
    u"""A globally scoped session.

    Register this as a global utility to have just one kind of session
    per Zope instance. All applications in this instance will share the
    same session.

    To register as a global utility you may need to register it with
    a custom factory, or alternatively subclass it and override __init__
    to pass the right arguments to the superclasses __init__.
    """
    interface.implements(sa_interfaces.IScopedSession)

    def sessionFactory(self):
        kw = self.kw.copy()
        if 'bind' not in kw:
            engine_factory = component.getUtility(
                sa_interfaces.IEngineFactory,
                name=self.engine
                )
            kw['bind'] = engine_factory()
        if 'user' not in kw:
            user_factory = component.getUtility(
                interfaces.ISessionUserFactory,
                name='occams.SessionUserFactory'
                )
            kw['user'] = user_factory
        if 'class_' not in kw:
            kw['class_'] = DataStoreSession
        return orm.scoped_session(orm.sessionmaker(**kw))


class SessionUserFactory(object):
    u"""
    Needs to be called "occams.SessionUserFactory"
    """
    interface.implements(interfaces.ISessionUserFactory)

    def __call__(self):
        u"""
        Get the id of the current user
        """
        return getSecurityManager().getUser().getId()


def handle_login(event):
    u"""
    Registers a user when they log in
    """
    for name, utility in component.getUtilitiesFor(sa_interfaces.IScopedSession):
        if name.find('occams') >= 0:
            principal = event.principal.getId()
            session = saconfig.named_scoped_session(name)
            try:
                user = session.query(model.User).filter_by(key=principal).one()
            except orm.exc.NoResultFound:
                # no user found, register into datastore accountability table
                user = model.User(key=principal)
                session.add(user)
                session.flush()
            except sa.exc.ProgrammingError, sa.exc.OperationalError:
                # no occams repository, ignore
                pass
