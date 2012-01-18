import unittest2 as unittest

import zope.schema
from zope.publisher.browser import TestRequest
from z3c.form.interfaces import ITextAreaWidget

from occams.form.interfaces import TEXTAREA_SIZE
from occams.form.browser.widgets import TextAreaFieldWidget
from occams.form.testing import OCCAMS_FORM_INTEGRATION_TESTING


class TestWidgets(unittest.TestCase):

    layer = OCCAMS_FORM_INTEGRATION_TESTING

    def assertTextArea(self, field):
        request = TestRequest()
        widget = TextAreaFieldWidget(field, request)

        if not ITextAreaWidget.providedBy(widget):
            self.fail('Not a text area!')

        if TEXTAREA_SIZE != widget.rows:
            self.fail('Incorrect text area size!')

    def testTextAreaField(self):
        self.assertTextArea(zope.schema.Text(__name__='foo', title=u'foo'))
        self.assertTextArea(zope.schema.ASCII(__name__='foo', title=u'foo'))
