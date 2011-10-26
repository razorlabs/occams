""" 
Application layers
"""
from plone.testing import Layer
        
TEST_LAYER = Layer(name='hive.roster:testlayer')

# class DataBaseLayer(Layer):
#     """ 
#     DataBase application layer for tests.
#     """

#     def setUp(self):
#         """ 
#         Creates the database structures.
#         """
#         engine = create_engine(CONFIG_URL, echo=CONFIG_ECHO)
#         model.Model.metadata.create_all(engine, checkfirst=True)
#         factory = sessionmaker(engine, autoflush=False, autocommit=False)
#         self['session'] = scoped_session(factory)

#     def tearDown(self):
#         """ 
#         Destroys the database structures.
#         """
#         model.Model.metadata.drop_all(self['session'].bind, checkfirst=True)
#         self['session'].close()
#         del self['session']

#     def testSetUp(self):
#         self['session'].rollback()

#     def testTearDown(self):
#         """ 
#         Cancels the transaction after each test case method.
#         """
#         self['session'].rollback()
        
# DATABASE_LAYER = DataBaseLayer()