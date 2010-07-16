from zope.interface import implements

from sqlalchemy import orm

from avrc.data.store import interfaces


class SessionFactory(object):
    """
    @see avrc.data.store.interfaces.ISessionFactory
    """

    implements(interfaces.ISessionFactory)
    
    def __init__(self, 
                 autocommit=False, 
                 autoflush=True, 
                 twophase=False, 
                 binds=None):
        """
        Our ISessionFactory implementation takes an extra parameter which 
        will be the database bindings.
        """
        self.autocommit = autocommit
        self.autoflush = autoflush
        self.twophase = twophase
        self.binds = binds
    
    def __call__(self):
        """
        Creates the Session object and binds it to the appropriate databases.
        """
        Session  = orm.scoped_session(orm.sessionmaker(
            autocommit=self.autocommit,
            autoflush=self.autoflush,
            twophase=self.twophase
            ))
        
        Session.configure(binds=self.binds)
        
        return Session