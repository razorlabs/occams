
import unittest

from avrc.data.store import model
from avrc.data.store.schema import HierarchyInspector

from avrc.data.store.tests.layers import DataBaseLayer


def createSchema(name, base=None):
    return model.Schema(base_schema=base, name=name, title=unicode(name))


class HierarchyTestCase(unittest.TestCase):
    """ 
    Verifies hierarchy listings of Zope schemata.
    """

    layer = DataBaseLayer


    def setUp(self):
        session = self.layer.session

        animal = createSchema('Animal')

        bird = createSchema('Bird', animal)
        reptile = createSchema('Reptile', animal)
        mammal = createSchema('Mammal', animal)
        amphibian = createSchema('Amphibian', animal)

        session.add_all([
            createSchema('Hawk', bird),
            createSchema('Chicken', bird),
            createSchema('Goose', bird),
            createSchema('Sparrow', bird),

            createSchema('Snake', reptile),
            createSchema('Lizard', reptile),
            createSchema('Turtle', reptile),

            createSchema('Mouse', mammal),
            createSchema('Dog', mammal),
            createSchema('Cat', mammal),

            createSchema('Frog', amphibian),
            createSchema('Salamander', amphibian),
            ])

        session.flush()

        self.hierarchy = HierarchyInspector(session)


    def tearDown(self):
        self.hierarchy = None


    def test_get_children(self):
        hierarchy = self.hierarchy
        names = hierarchy.getChildren('Bird')
        self.assertEqual(4, len(names))


    def test_get_children_names(self):
        hierarchy = self.hierarchy

        result = hierarchy.getChildrenNames('Bird')
        names = [n for (n, t) in result]
        self.assertEqual(4, len(names))
        self.assertTrue('Hawk' in names)
        self.assertTrue('Chicken' in names)
        self.assertTrue('Goose' in names)
        self.assertTrue('Sparrow' in names)

        names = hierarchy.getChildrenNames('Fish')
        self.assertEqual(0, len(names))

        names = hierarchy.getChildrenNames('Animal')
        self.assertEqual(12, len(names))

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
