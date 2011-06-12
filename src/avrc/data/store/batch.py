
import zope.interface
from zope.schema.fieldproperty import FieldProperty
from zope.interface.common.sequence import IFiniteSequence

from z3c.batching import interfaces
from z3c.batching import batch

class SqlBatch(batch.Batch):
    """Batch implementation for sqlalchemy. See IBatch"""

    zope.interface.implements(interfaces.IBatch)

    start = FieldProperty(interfaces.IBatch['start'])
    size = FieldProperty(interfaces.IBatch['size'])
    end = FieldProperty(interfaces.IBatch['end'])

    def __init__(self, query, start=0, size=20, batches=None):
        self.query = query
        length = query.count()
        self._length = length

        # See interfaces.IBatch
        self.start = start
        if length == 0:
            self.start = -1
        elif start >= length:
            raise IndexError('start index key out of range')

        # See interfaces.IBatch
        self.size = size
        self._trueSize = size

        if start + size >= length:
            self._trueSize = length - start

        # See interfaces.IBatch
        if length == 0:
            self.end = -1
        else:
            self.end = start + self._trueSize - 1

        if batches is None:
            batches = SqlBatches(self)

        self.batches = batches

    @property
    def firstElement(self):
        """See interfaces.IBatch"""
        query = self.query.offset(self.start)
        rslt = query.first()
        obj = rslt.objectify()
        return (rslt.id, obj)

    @property
    def lastElement(self):
        """See interfaces.IBatch"""
        query = self.query.offset(self.end)
        rslt = query.first()
        obj = rslt.objectify()
        return (rslt.id, obj)

    def __getitem__(self, key):
        """See zope.interface.common.sequence.IMinimalSequence"""
        if key >= self._trueSize:
            raise IndexError('batch index out of range')
        query = self.query.offset(self.start+key)
        rslt = query.first()
        obj = rslt.objectify()
        return (rslt.id, obj)

    def __iter__(self):
        """See zope.interface.common.sequence.IMinimalSequence"""
        if self._length>0:            
            query = self.query.slice(self.start, self.end+1)
            return iter((rslt.id, rslt.objectify()) for rslt in  query.all())
        else:
            return iter([])

    def __len__(self):
        """See zope.interface.common.sequence.IFiniteSequence"""
        return self._trueSize

    def __contains__(self, item):
        for i in self:
            if item == i:
                return True
        else:
            return False

    def __getslice__(self, i, j):
        if j > self.end:
            j = self._trueSize
        query = self.query.slice(i,j)
        yield (rslt.id, rslt.objectify()) in query.all()
        
    def __eq__(self, other):
        return ((self.size, self.start, self.query) ==
                (other.size, other.start, other.query))


class SqlBatches(batch.Batches):
    """A sequence object representing all the batches.
       Used by a Batch.
    """
    zope.interface.implements(IFiniteSequence)

    def __init__(self, batch):
        self.size = batch.size
        self.total = batch.total
        self.query = batch.query
        self._batches = {batch.index: batch}

    def __getitem__(self, key):
        if key not in self._batches:
            if key < 0:
                key = self.total + key

            batch = Batch(
                self.query, key*self.size, self.size, self)
            self._batches[batch.index] = batch

        try:
            return self._batches[key]
        except KeyError:
            raise IndexError(key)
