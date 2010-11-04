#    def test_search(self):
#        """
#        """
#        dsn = u"sqlite:///test.db"
#        #dsn = u"sqlite:///:memory:"
#        ds = datastore.Datastore(title=u"blah", dsn=dsn)
#
#        ds.schema.put(testing.IStandaloneInterface)
#
#        # just get everything
#        results_obj = ds.search.by_base(4, 10)
#
#        print
#        print results_obj
#        print
#
#        self.fail("Search Complete")