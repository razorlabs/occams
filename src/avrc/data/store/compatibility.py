
from zope.interface.interface import InterfaceClass
from avrc.data.store import directives
from avrc.data.store import model


def schema2iface(session, schema):
    # Process the base classes first
    if schema.base_schema:
        ibase = schema2iface(schema.base_schema)
    else:
        ibase = directives.Schema

    iface = InterfaceClass(
        name=str(schema.name),
        bases=[ibase],
        attrs=[attribute2field(a) for a in schema.attributes],
        )

    directives.__id__.set(iface, schema.id)
    directives.title.set(iface, schema.title)
    directives.description.set(iface, schema.description)
    directives.version.set(iface, schema.create_date)

    return iface

def iface2schema(session, iface):
    if not directives.Schema.isEqualOrExtendedBy(iface):
        raise ValueError('%s is not a child class of %s' % (iface, directives.Schema))

    if 1 < len(iface.__bases__):
        raise MultipleBasesError
    elif 1 == len(iface.__bases__) and directives.Schema != iface.__bases__[0]:
        base_schema = iface2schema(session, iface.__bases__[0])
    else:
        base_schema = None

    schema = model.Schema(base_schema=base_schema, name=key)
    session.add(schema)

    schema.title = directives.title.bind().get(item)
    schema.description = directives.description.bind().get(item)
    if schema.description is not None:
        # Sanitize the description (i.e. make sure no empty strings)
        schema.description = schema.description.strip() or None
    session.flush()

    directives.__id__.set(item, schema.id)
    directives.version.set(item, schema.create_date)

    manager = FieldManager(schema)
    for order, field in enumerate(zope.schema.getFieldsInOrder(item), start=0):
        (name, field) = field
        field.order = order # sanitize the order
        manager.put(name, field)

    return schema.id

def attribute2field(session, field):
    pass
