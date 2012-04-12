
from zope.interface import implements
from zope.schema.fieldproperty import FieldProperty
from zope.interface.common.sequence import IFiniteSequence

from z3c.batching.interfaces import IBatch
from z3c.batching.batch import Batch
from z3c.batching.batch import Batches


class SqlBatch(Batch):
    """
    Batch implementation for sqlalchemy.
    See IBatch
    """

    implements(IBatch)

    start = FieldProperty(IBatch['start'])
    size = FieldProperty(IBatch['size'])
    end = FieldProperty(IBatch['end'])

    def __init__(self, query, start=0, size=20, batches=None):
        length = query.count()

        if length == 0:
            start = -1

        if start >= length:
            raise IndexError('start index key out of range')

        # trueSize is the number of remaining items in the current batch
        if start + size >= length:
            trueSize = length - start
        else:
            trueSize = size

        if length == 0:
            end = -1
        else:
            end = start + trueSize - 1

        self.start = start
        self.end = end
        self.size = size

        # The thing we're iterating with
        self.query = query

        # Required for internals to work
        self._length = length
        self._trueSize = trueSize

        if batches is None:
            batches = SqlBatches(self)

        self.batches = batches

    @property
    def firstElement(self):
        """
        See interfaces.IBatch
        """
        result = self.query.offset(self.start).limit(1).one()
        if hasattr(result, 'objectify'):
            result = result.objectify()
        return (result.id, result)

    @property
    def lastElement(self):
        """
        See interfaces.IBatch
        """
        result = self.query.offset(self.end).limit(1).one()
        if hasattr(result, 'objectify'):
            result = result.objectify()
        return (result.id, result)

    def __getitem__(self, key):
        """
        See zope.interface.common.sequence.IMinimalSequence
        """
        if key >= self._trueSize:
            raise IndexError('batch index out of range')
        result = self.query.offset(self.start + key).limit(1).one()
        if hasattr(result, 'objectify'):
            result = result.objectify()
        return (result.id, result)

    def __iter__(self):
        """
        See zope.interface.common.sequence.IMinimalSequence
        """
        if self._length > 0:
            for result in self.query.slice(self.start, self.end + 1):
                if hasattr(result, 'objectify'):
                    result = result.objectify()
                yield (result.id, result)

    def __len__(self):
        """
        See zope.interface.common.sequence.IFiniteSequence
        """
        return self._trueSize

    def __contains__(self, item):
        return (item.id, item) in iter(self)

    def __getslice__(self, i, j):
        if j > self.end:
            j = self._trueSize
        query = self.query.slice(i, j)
        for result in query:
            if hasattr(result, 'objectify'):
                result = result.objectify()
            yield (result.id, result)

    def __eq__(self, other):
        return ((self.size, self.start, self.query) ==
                (other.size, other.start, other.query))


class SqlBatches(Batches):
    """
    A sequence object representing all the batches.
    Used by a Batch.
    """
    implements(IFiniteSequence)

    def __init__(self, batch):
        self.size = batch.size
        self.total = batch.total
        self.query = batch.query
        self._batches = {batch.index: batch}

    def __getitem__(self, key):
        """
        Raises:
            ``IndexError``
        """
        if key not in self._batches:
            if key < 0:
                key = self.total + key
            batch = SqlBatch(self.query, key * self.size, self.size, self)
            self._batches[batch.index] = batch
        return self._batches[key]
