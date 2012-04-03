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
from occams.datastore.interfaces import XmlError


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
            E.attributes(*[attributeToXml(a) for a in schema.attributes.values()])
            )

    return xschema


def attributeToXml(attribute):
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
        xattribute.append(schemaToXml(attribute.object_schema))

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
        xattribute.append(E.choices(*[choiceToXml(c) for c in attribute.choices]))

    return xattribute


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

    parser = lxml.etree.XMLParser(remove_blank_text=True)

    if isinstance(file_, basestring):
        with open(file_) as in_:
            tree = lxml.objectify.parse(in_)
    else:
        tree = lxml.objectify.parse(file_)

    xschema = tree.getroot()
    schema = xmlToSchema(xschema)

    try:
        session.add(schema)
        session.flush()
    except IntegrityError:
        raise
#        raise AlreadyExistsError(model.Schema, (schema.name, schema.publish_date,))

    return schema


def xmlToSchema(element):
    """
    Converts an XML file into a schema

    Arguments
        ``file_``
            The filename or file object to import from
    """

    schema = model.Schema(
        name=element.attrib['name'],
        title=element.title,
        description=getattr(element, 'description', None),
        state='published',
        publish_date=datetime.strptime(element.attrib['published'], '%Y-%m-%d').date(),
        storage=element.attrib['storage'],
        )

    if 'inline' in element.attrib:
        schema.is_inline = element.attrib['inline'].lower()[0] in ('1', 't'),

    for xattribute in getattr(element, 'attributes', []):
        attribute = elementToAttribute(xattribute)
        schema[attribute.name] = attribute

    return schema


def elementToAttribute(element):
    pass


def elementToChoice(element):
    pass

