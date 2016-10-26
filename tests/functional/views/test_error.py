class Test_urldecode_error:

    def test_reject_non_unicode_params(self, app):
        """
        It should return 'Bad Request' when it encounters a non-unicode URL
        """
        res = app.get('/%80', expect_errors=True)
        assert res.status_code == 400
