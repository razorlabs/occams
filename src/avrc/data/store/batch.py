
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
        self.query = query
        length = query.count()
        self._length = length

        self.start = start
        if length == 0:
            self.start = -1
        elif start >= length:
            raise IndexError('start index key out of range')

        self.size = size
        self._trueSize = size

        if start + size >= length:
            self._trueSize = length - start

        if length == 0:
            self.end = -1
        else:
            self.end = start + self._trueSize - 1

        if batches is None:
            batches = SqlBatches(self)

        self.batches = batches


    @property
    def firstElement(self):
        """
        See interfaces.IBatch
        """
        query = self.query.offset(self.start)
        result = query.first()
        if hasattr(result, 'objectify'):
            result = result.objectify()
        return (result.id, result)


    @property
    def lastElement(self):
        """
        See interfaces.IBatch
        """
        query = self.query.offset(self.end)
        result = query.first()
        if hasattr(result, 'objectify'):
            result = result.objectify()
        return (result.id, result)


    def __getitem__(self, key):
        """
        See zope.interface.common.sequence.IMinimalSequence
        """
        if key >= self._trueSize:
            raise IndexError('batch index out of range')
        query = self.query.offset(self.start + key)
        result = query.first()
        if hasattr(result, 'objectify'):
            result = result.objectify()
        return (result.id, result)


    def __iter__(self):
        """
        See zope.interface.common.sequence.IMinimalSequence
        """
        if self._length > 0:
            query = self.query.slice(self.start, self.end + 1)
            for result in query.all():
                if hasattr(result, 'objectify'):
                    result = result.objectify()
                yield (result.id, result)


    def __len__(self):
        """
        See zope.interface.common.sequence.IFiniteSequence
        """
        return self._trueSize


    def __contains__(self, item):
        return item in iter(self)


    def __getslice__(self, i, j):
        if j > self.end:
            j = self._trueSize
        query = self.query.slice(i, j)
        for result in query.all():
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
            batch = Batch(self.query, key * self.size, self.size, self)
            self._batches[batch.index] = batch
        return self._batches[key]
