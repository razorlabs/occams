import sys
import pytest

@pytest.mark.skip("""
    These tests used to fail in Python 2 due to bad encodings.
    Keeping them for historical reference.
""")
class Test_urldecode_error:

    def test_reject_non_unicode_params(self, testapp):
        """
        It should return 'Bad Request' when it encounters a non-unicode URL
        """
        res = testapp.get('/%80', expect_errors=True)
        assert res.status_code == 400
