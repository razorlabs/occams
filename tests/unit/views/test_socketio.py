import pytest


@pytest.yield_fixture
def spawn(config):
    import mock
    name = 'occams_studies.views.socketio.ExportNamespace.spawn'
    with mock.patch(name) as patch:
        yield patch


@pytest.yield_fixture
def emit(config):
    import mock
    name = 'occams_studies.views.socketio.ExportNamespace.emit'
    with mock.patch(name) as patch:
        yield patch


class TestExportNameSpace:

    def test_initalize_not_allowed(self, req, db_session, spawn):
        """
        It should keep methods protected if the user does not have permissions
        """
        import mock
        from occams_studies.views.socketio import ExportNamespace

        req.has_permission = mock.Mock(return_value=False)
        req.redis = mock.Mock()
        req.environ = {'socketio': mock.Mock(session={})}
        ns = ExportNamespace(req.environ, '/export', req)
        ns.initialize()

        req.has_permission.assert_called_with('view', mock.ANY)
        assert 'user' not in ns.session
        assert 'redis' not in ns.session

    def test_initalize_allowed(self, req, db_session, config, spawn):
        """
        It should unlock methods if the user has the proper permissions
        """
        import mock
        from occams_studies.views.socketio import ExportNamespace

        config.testing_securitypolicy(userid='joe', permissive=True)

        req.has_permission = mock.Mock(return_value=True)
        req.redis = mock.Mock()
        req.environ = {'socketio': mock.Mock(session={})}
        ns = ExportNamespace(req.environ, '/export', req)
        ns.initialize()

        req.has_permission.assert_called_with('view', mock.ANY)
        assert ns.session['user'] == 'joe'
        assert 'redis' in ns.session
        spawn.assert_called_once_with(ns.listener)

    def test_initially_locked(self, req, db_session):
        """
        It should initially lock all access to methods
        """
        import mock
        from occams_studies.views.socketio import ExportNamespace
        req.environ = {'socketio': mock.Mock(session={})}
        ns = ExportNamespace(req.environ, '/export', req)
        assert ns.get_initial_acl() == []

    def test_listener_broadcast(self, req, db_session, emit):
        """
        It should emit ongoing progress for the authenticated user
        """
        import json
        import mock
        from occams_studies.views.socketio import ExportNamespace

        def listen():
            return [
                {'type': 'blah', 'data': 'stuff'},
                {'type': 'message',
                 'data': json.dumps({'owner_user': 'jane', 'export_id': 123})},
                {'type': 'message',
                 'data': json.dumps({'owner_user': 'joe', 'export_id': 345})}]

        req.has_permission = mock.Mock(return_value=True)
        req.redis = mock.Mock(pubsub=lambda: mock.Mock(listen=listen))
        req.environ = {'socketio': mock.Mock(session={})}
        ns = ExportNamespace(req.environ, '/export', req)
        ns.session['user'] = 'jane'
        ns.session['redis'] = req.redis
        ns.listener()

        emit.assert_called_once_with(
            'export',
            {'export_id': 123,
             'owner_user': 'jane'})
