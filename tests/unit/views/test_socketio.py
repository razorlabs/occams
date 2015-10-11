import mock

from tests import IntegrationFixture


class TestExportNameSpace(IntegrationFixture):

    @mock.patch('occams_studies.views.socketio.ExportNamespace.spawn')
    def test_initalize_not_allowed(self, spawn):
        """
        It should keep methods protected if the user does not have permissions
        """
        from pyramid import testing
        from occams_studies.views.socketio import ExportNamespace

        request = testing.DummyRequest(
            has_permission=mock.Mock(return_value=False),
            redis=mock.Mock(),
            environ={'socketio': mock.Mock(session={})})
        ns = ExportNamespace(request.environ, '/export', request)
        ns.initialize()

        request.has_permission.assert_called_with('view', mock.ANY)
        self.assertNotIn('user', ns.session)
        self.assertNotIn('redis', ns.session)

    @mock.patch('occams_studies.views.socketio.ExportNamespace.spawn')
    def test_initalize_allowed(self, spawn):
        """
        It should unlock methods if the user has the proper permissions
        """
        from pyramid import testing
        from occams_studies.views.socketio import ExportNamespace

        self.config.testing_securitypolicy(userid='joe', permissive=True)

        request = testing.DummyRequest(
            has_permission=mock.Mock(return_value=True),
            redis=mock.Mock(),
            environ={'socketio': mock.Mock(session={})})
        ns = ExportNamespace(request.environ, '/export', request)
        ns.initialize()

        request.has_permission.assert_called_with('view', mock.ANY)
        self.assertEquals(ns.session['user'], 'joe')
        self.assertIn('redis', ns.session)
        spawn.assert_called_once_with(ns.listener)

    def test_initially_locked(self):
        """
        It should initially lock all access to methods
        """
        from pyramid import testing
        from occams_studies.views.socketio import ExportNamespace
        request = testing.DummyRequest(
            environ={'socketio': mock.Mock(session={})})
        ns = ExportNamespace(request.environ, '/export', request)
        self.assertItemsEqual([], ns.get_initial_acl())

    @mock.patch('occams_studies.views.socketio.ExportNamespace.emit')
    def test_listener_broadcast(self, emit):
        """
        It should emit ongoing progress for the authenticated user
        """
        import json
        from pyramid import testing
        from occams_studies.views.socketio import ExportNamespace

        def listen():
            return [
                {'type': 'blah', 'data': 'stuff'},
                {'type': 'message',
                 'data': json.dumps({'owner_user': 'jane', 'export_id': 123})},
                {'type': 'message',
                 'data': json.dumps({'owner_user': 'joe', 'export_id': 345})}]

        request = testing.DummyRequest(
            has_permission=mock.Mock(return_value=True),
            redis=mock.Mock(
                pubsub=lambda: mock.Mock(listen=listen)),
            environ={'socketio': mock.Mock(session={})})
        ns = ExportNamespace(request.environ, '/export', request)
        ns.session['user'] = 'jane'
        ns.session['redis'] = request.redis
        ns.listener()

        emit.assert_called_once_with(
            'export',
            {'export_id': 123,
             'owner_user': 'jane'})
