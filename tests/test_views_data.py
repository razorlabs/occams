from unittest import TestCase

from tests import ClinicalFunctionalFixture


class TestList(ClinicalFunctionalFixture, TestCase):

    def test_view(self):
        response = self.app.get('/data/')
        self.assertTrue(b'hello' in response.body)
