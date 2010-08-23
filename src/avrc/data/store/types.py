"""
"""
from zope.interface import implements
import zope.schema
from zope.schema.vocabulary import SimpleVocabulary

from avrc.data.store import interfaces

class Range(zope.schema.Tuple):
    implements(interfaces.IRange)

    __doc__ = interfaces.IRange.__doc__

    def _validate(self, value):
        """
        """
        super(Range, self)._validate(value)

        try:
            (low, high) = value
        except ValueError as e:
            raise Exception("Range value is invalid: %s" % e)

supported_types_vocabulary = SimpleVocabulary.fromItems([
    ("integer", zope.schema.Int),
    ("string", zope.schema.TextLine),
    ("text", zope.schema.Text),
    ("binary", zope.schema.Bytes),
    ("boolean", zope.schema.Bool),
    ("real", zope.schema.Decimal),
    ("date", zope.schema.Date),
    ("datetime", zope.schema.Datetime),
    ("time", zope.schema.Time),
    ("object", zope.schema.Object),
    ("selection", zope.schema.Choice),
    ("range", Range),
    ])