import six
import wtforms
from wtforms.utils import unset_value

from .widgets import FileInput


class FileField(wtforms.Field):
    """
    Custom multi-input field for updating file upload fields
    """

    widget = FileInput()

    def _value(self):
        """
        Renders the data to markup value
        """
        return six.text_type(self.data) if self.data is not None else ''

    def process(self, formdata, data=unset_value):
        """
        Processes raw form data

        Overrides: wtforms.Field.process to handle multiple input sources.
        http://wtforms.readthedocs.org/en/latest/fields.html#considerations-for-overriding-process
        """

        if not formdata:
            self.data = data if data is not unset_value else None
            return

        raw_previous = formdata.getlist('%s-previous' % self.name)
        raw_new = formdata.getlist('%s-new' % self.name)

        try:
            previous = bool(int(raw_previous[0]))
        except (KeyError, IndexError, ValueError):
            previous = False

        try:
            new = raw_new[0]
        except IndexError:
            new = None

        if hasattr(new, 'file'):
            self.data = new
        elif previous:
            self.data = data
        else:
            self.data = None
