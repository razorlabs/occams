
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
        """
        Tweak the original ``Batch.__init__`` to accommodate SQL queries
        """
        self.query = query

        length = query.count()

        # See interfaces.IBatch
        if length == 0:
            # Some SQL vendors don't like negatives so floor it to zero
            start = 0
        elif start >= length:
            raise IndexError('start index key out of range')

        # See interfaces.IBatch
        if start + size >= length:
            trueSize = length - start
        else:
            trueSize = size

        # See interfaces.IBatch
        if length == 0:
            # Same thing as start
            end = 0
        else:
            end = start + trueSize - 1

        self._trueSize = trueSize
        self.size = size
        self.start = start
        self.end = end
        self._length = length
        self.batches = batches or SqlBatches(self)

    @property
    def firstElement(self):
        """
        See interfaces.IBatch
        """
        result = self.query.offset(self.start).limit(1).one()
        return (getattr(result, 'id', 1), result)

    @property
    def lastElement(self):
        """
        See interfaces.IBatch
        """
        result = self.query.offset(self.end).limit(1).one()
        return (getattr(result, 'id', 1), result)

    def __getitem__(self, key):
        """
        See zope.interface.common.sequence.IMinimalSequence
        """
        if key >= self._trueSize:
            raise IndexError('batch index out of range')
        if key < 0:
            if self._trueSize > 0:
                key = self._trueSize + key
            else:
                # the batch since is empty and so we can't access any item
                raise IndexError('batch index out of range')
        result = self.query.offset(key).limit(1).one()
        return (getattr(result, 'id', 1), result)

    def __iter__(self):
        """
        See zope.interface.common.sequence.IMinimalSequence
        """
        if self._length > 0:
            for res_count, result in enumerate(self.query.slice(self.start, self.end + 1)):
                yield (getattr(result, 'id', res_count), result)

    def __len__(self):
        """
        See zope.interface.common.sequence.IFiniteSequence
        """
        return self._trueSize

    def __contains__(self, item):
        return (item.id, item) in iter(self)

    def __getslice__(self, i, j):
        # note: python adjusts the index, but it may still be negative
        # (e.g. if the negative number is larger than the whole list)
        if i < 0:
            i = 0
        if j > self.end:
            j = self._trueSize
        if j < i:
            # stop value may not be less than the index
            j = i
        query = self.query.slice(i, j)
        for res_count, result in enumerate(query):
            yield (getattr(result, 'id', res_count), result)

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
