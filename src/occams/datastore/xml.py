"""
Import/Export functionality of schemata via XML files
"""

from datetime import datetime
import lxml.etree
import lxml.objectify
from lxml.builder import ElementMaker
from sqlalchemy.exc import IntegrityError

from occams.datastore import model
from occams.datastore.interfaces import AlreadyExistsError


E = ElementMaker(nsmap={None : 'http://bitcore.ucsd.edu/occams/datastore'})


def exportToXml(schema, file_):
    """
    Exports the schema to a specified XML file.

    Arguments
        ``schema``
            The schema to export
        ``file_``
            The filename or file object to write to
    """

    xml = schemaToElement(schema)
    xml.insert(0, lxml.etree.Comment('Generated: %s' % datetime.now()))
    content = lxml.etree.tounicode(xml)

    if isinstance(file_, basestring):
        with open(file_) as out:
            out.write(content)
    else:
        file_.write(content)


def schemaToElement(schema):
    """
    Converts a schema into an XML element tree
    """

    xschema = E.schema(
        E.title(schema.title),
        name=schema.name,
        storage=schema.storage,
        published=schema.publish_date.strftime('%Y-%m-%d')
        )

    if schema.is_inline:
        xschema.set('inline', str(schema.is_inline))

    if schema.description is not None:
        xschema.append(E.description(schema.description or ''))

    if schema.attributes:
        xschema.append(
            E.attributes(*[attributeToElement(a) for a in schema.attributes.values()])
            )

    return xschema


def attributeToElement(attribute):
    """
    Converts an attribute into an XML element tree
    """

    xattribute = E.attribute(
        E.checksum(attribute.checksum),
        E.title(attribute.title),
        name=attribute.name,
        type=attribute.type,
        required=str(attribute.is_required),
        )

    if attribute.description is not None:
        xattribute.append(E.description(attribute.description))

    if attribute.type == 'object':
        # Continue processing subschemata recursively
        xattribute.append(schemaToElement(attribute.object_schema))

    if attribute.is_collection:
        ecollection = E.collection()
        if attribute.collection_min:
            ecollection.min = attribute.collection_min
        if attribute.collection_max:
            ecollection.max = attribute.collection_max
        attribute.append(ecollection)

    if attribute.value_min is not None or attribute.value_max is not None:
        elimit = E.limit()
        if attribute.value_min is not None:
            elimit.min = attribute.value_min
        if attribute.value_max is not None:
            elimit.max = attribute.value_min
        attribute.append(elimit)

    if attribute.validator:
        attribute.append(E.validator(attribute.validator))

    if attribute.choices:
        xattribute.append(E.choices(*[choiceToElement(c) for c in attribute.choices]))

    return xattribute


def choiceToElement(choice):
    """
    Converts a choice into an XML element tree
    """
    return E.choice(choice.title, value=choice._value,)


def importFromXml(session, file_):
    """
    Imports the specified XML file into the session

    Arguments
        ``session``
            The database session to import into
        ``file_``
            The filename or file object to import from

    Raises
        ``SchemaAlreadyExistsError`` if the schema already exists
    """

    if isinstance(file_, basestring):
        with open(file_) as in_:
            tree = lxml.objectify.parse(in_)
    else:
        tree = lxml.objectify.parse(file_)

    xschema = tree.getroot()
    schema = elementToSchema(xschema)

    try:
        session.add(schema)
        session.flush()
    except IntegrityError as e:
        if 'unique' in e.message:
            e = AlreadyExistsError(model.Schema, schema.name, schema.publish_date)
        raise e

    return schema


def elementToSchema(element):
    """
    Converts a schema XML element into a sqlalchemy ``Schema`` instance
    """
    schema = model.Schema(
        name=str(element.attrib['name']),
        title=unicode(element.title),
        state='published',
        publish_date=datetime.strptime(element.attrib['published'], '%Y-%m-%d').date(),
        storage=str(element.attrib['storage']),
        )

    if hasattr(element, 'description'):
        schema.description = str(element.description)

    if 'inline' in element.attrib:
        schema.is_inline = element.attrib['inline'].lower()[0] in ('1', 't'),

    for index, xattribute in enumerate(getattr(element, 'attributes', [])):
        attribute = elementToAttribute(xattribute)
        attribute.order = index
        schema[attribute.name] = attribute

    return schema


def elementToAttribute(element):
    """
    Converts an attribute XML element into a sqlalchemy ``Attribute`` element
    """

    attribute = model.Attribute(
        name=str(element.attr['name']),
        title=unicode(element.title),
        type=str(element.attr['type']),
        is_required=str(element.attr['required']).lower()[0] in ('t', '1'),
        )

    if hasattr(element, 'description'):
        attribute.description = unicode(element.description)

    if hasattr(element, 'checksum'):
        attribute.checksum = str(element.checksum)

    if attribute.type == 'object':
        attribute.object_schema = elementToSchema(element.schema)

    if hasattr(element, 'collection'):
        attribute.is_collection = True
        if 'min' in element.collection.attr:
            attribute.collection_min = int(element.collection.attr['min'])
        if 'max' in element.collection.attr:
            attribute.collection_max = int(element.collection.attr['max'])

    if hasattr(element, 'limit'):
        if 'min' in element.limit.attr:
            attribute.value_min = int(element.limit.attr['min'])
        if 'max' in element.limit.attr:
            attribute.value_max = int(element.limit.attr['max'])

    if hasattr(element, 'validator'):
        attribute.validator = str(element.validator)

    for index, xchoice in enumerate(getattr(element, 'choices', [])):
        choice = elementToChoice(xchoice)
        choice.order = index
        attribute.choices.append(choice)

    return attribute


def elementToChoice(element):
    """
    Converts a choice XML element into a sqlalchemy ``Choice`` instance
    """
    return model.Choice(
        title=unicode(element.title),
        _value=unicode(element.attr['value']),
        )
