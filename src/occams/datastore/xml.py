"""
Import/Export functionality of schemata via XML files
"""

from datetime import datetime
import lxml.etree
from lxml.builder import ElementMaker

from occams.datastore.schema import SchemaManager
from occams.datastore.interfaces import ManagerKeyError


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

    xml = schemaToXml(schema)
    xml.insert(0, lxml.etree.Comment('Generated: %s' % datetime.now()))
    content = lxml.etree.tounicode(xml)

    if isinstance(file_, basestring):
        with open(file_) as out:
            out.write(content)
    else:
        file_.write(content)


def schemaToXml(schema):
    """
    Converts a schema into an XML element tree
    """

    eschema = E.schema(
        E.title(schema.title),
        name=schema.name,
        storage=schema.storage,
        inline=str(schema.is_inline),
        published=schema.publish_date.strftime('%Y-%m-%d')
        )

    if schema.description is not None:
        eschema.append(E.description(schema.description or ''))

    if schema.attributes:
        eschema.append(
            E.attributes(*[attributeToXml(a) for a in schema.attributes.values()])
            )

    return eschema


def attributeToXml(attribute):
    """
    Converts an attribute into an XML element tree
    """

    eattribute = E.attribute(
        E.checksum(attribute.checksum),
        E.title(attribute.title),
        name=attribute.name,
        type=attribute.type,
        required=str(attribute.is_required),
        )

    if attribute.description is not None:
        eattribute.append(E.description(attribute.description))

    if attribute.type == 'object':
        # Continue processing subschemata recursively
        eattribute.append(schemaToXml(attribute.object_schema))

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
        eattribute.append(E.choices(*[choiceToXml(c) for c in attribute.choices]))

    return eattribute


def choiceToXml(choice):
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
            tree = lxml.etree.parse(in_)
    else:
        tree = lxml.etree.parse(file_)

    manager = SchemaManager(session)
    eschema = tree.getroot()

    try:
        publish_date = datetime.strptime('%Y-%m-%d', eschema.publish_date).date()
        schema = manager.get(eschema.name, publish_date)
    except ManagerKeyError:
        schema = xmlToSchema(eschema)
        manager.put(schema)

    return schema


def xmlToSchema(xml):
    """
    Converts an XML file into a schema

    Arguments
        ``file_``
            The filename or file object to import from
    """


def elementToAttribuet(element):
    pass


def elementToChoice(element):
    pass

