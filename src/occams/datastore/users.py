from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import Session
from zope.component import adapts
from zope.interface import classProvides
from zope.interface import implements

from occams.datastore import model
from occams.datastore.interfaces import ManagerKeyError
from occams.datastore.interfaces import IUserManager
from occams.datastore.interfaces import IUserManagerFactory


class UserManager(object):
    classProvides(IUserManagerFactory)
    implements(IUserManager)
    adapts(Session)

    __doc__ = IUserManager.__doc__

    def __init__(self, session):
        self.session = session

    __init__.__doc__ = IUserManagerFactory['__call__'].__doc__

    def keys(self):
        query = self.session.query(model.User).order_by('key')
        return [i.name for i in iter(query)]

    keys.__doc__ = IUserManager['keys'].__doc__

    def has(self, key):
        return self.session.query(model.User).filter_by(key=key).count() > 0

    has.__doc__ = IUserManager['has'].__doc__

    def purge(self, key):
        return self.session.query(model.User).filter_by(key=key).delete('fetch')

    purge.__doc__ = IUserManager['purge'].__doc__

    def get(self, key):
        try:
            user = self.session.query(model.User).filter_by(key=key).one()
        except NoResultFound:
            raise ManagerKeyError(model.User, key)
        else:
            return user

    get.__doc__ = IUserManager['get'].__doc__

    def put(self, key, item):
        session = self.session
        if item.key is None and key is None:
            raise ValueError
        elif item.key is None:
            item.key = key
        session.add(item)
        session.flush()
        return item.id

    put.__doc__ = IUserManager['put'].__doc__
