""" 
Checks for inconsistencies in the database
Experimental feature.
"""


from avrc.data.store import model


def checkNoOverlapDate(engine):
    """ 
    Checks that the tables have logically consistent and non-overlapping dates. 
    """


def checkValidChoiceValue(engine):
    """
    Checks that choice attributes have proper choice reference values.
    """


def checkValidEntityAttribute(engine):
    """ 
    Checks that an assignement's Entity/Attribute combination point to
    the same Schema.
    """


def checkCorrectChoiceOrder(engine):
    """ 
    Checks that choice vocabularies have consistent ordering.
    """


def checkCorrectAttributeOrder(engine):
    """ 
    Checks that attributes have consistent ordering.
    """


def checkCorrectTypeAssigment(engine):
    """ 
    Checks that the assignments have correct types.
    """


def checkNoAttributeWidget(engine):
    """ 
    Checks that the widget field in the Attribute table is not
    being used.
    """


def checkRequiredValues(engine):
    """ 
    Checks that instances have required values set.
    """


if __name__ == '__main__':
    pass
