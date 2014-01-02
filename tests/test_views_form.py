from unittest import TestCase

from tests import FormFunctionalFixture


class TestList(FormFunctionalFixture, TestCase):

    def test_view(self):
        response = self.app.get('/')
        self.assertTrue(b'hello' in response.body)
