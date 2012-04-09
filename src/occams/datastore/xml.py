"""
Import/Export functionality of schemata via XML files
"""

import codecs
from datetime import datetime
import lxml.etree
import lxml.objectify
from lxml.builder import ElementMaker
from sqlalchemy.exc import IntegrityError

from occams.datastore import model
from occams.datastore.interfaces import AlreadyExistsError


E = ElementMaker(nsmap={None : 'http://bitcore.ucsd.edu/occams/datastore'})


def exportXml(schema, file_):
    """
    Exports the schema to a specified UTF-8 encoding XML file.
    All files are exported to UTF-8 encoding to support multiple languages.

    Arguments
        ``schema``
            The schema to export
        ``file_``
            The filename or file object to write to
    """

    xschema = schemaToElement(schema)
    xschema.insert(0, lxml.etree.Comment('Generated: %s' % datetime.now()))
    content = lxml.etree.tostring(
        xschema,
        encoding=unicode,
        pretty_print=True,
        )

    if isinstance(file_, basestring):
        with codecs.open(file_, mode='w+b', encoding='utf-8') as stream:
            stream.write(content)
    else:
        file_.write(content)


def schemaToElement(schema):
    """
    Converts a published schema into an XML element tree
    """

    xschema = E.schema(
        E.title(schema.title),
        name=schema.name,
        storage=schema.storage,
        # Only published schemata are allowed to be serialized into XML, so
        # we only really need the date
        published=schema.publish_date.strftime('%Y-%m-%d')
        )

    if schema.description is not None:
        xschema.append(E.description(schema.description))

    if schema.attributes:
        xschema.append(E.attributes(*[attributeToElement(a) for a in schema.values()]))

    return xschema


def attributeToElement(attribute):
    """
    Converts an attribute into an XML element tree
    """

    xattribute = E.attribute(
        E.title(attribute.title),
        name=attribute.name,
        type=attribute.type,
        required=str(attribute.is_required),
        )

    if attribute.checksum:
        xattribute.append(E.checksum(attribute.checksum))

    if attribute.description is not None:
        xattribute.append(E.description(attribute.description))

    if attribute.type == 'object':
        # Continue processing subschemata recursively
        xattribute.append(schemaToElement(attribute.object_schema))

    if attribute.is_collection:
        xcollection = E.collection()
        if attribute.collection_min:
            xcollection.set('min', str(attribute.collection_min))
        if attribute.collection_max:
            xcollection.set('max', str(attribute.collection_max))
        xattribute.append(xcollection)

    if attribute.value_min is not None or attribute.value_max is not None:
        xlimit = E.limit()
        if attribute.value_min is not None:
            xlimit.set('min', str(attribute.value_min))
        if attribute.value_max is not None:
            xlimit.set('max', str(attribute.value_min))
        xattribute.append(xlimit)

    if attribute.validator:
        xattribute.append(E.validator(attribute.validator))

    if attribute.choices:
        xattribute.append(E.choices(*[choiceToElement(c) for c in attribute.choices]))

    return xattribute


def choiceToElement(choice):
    """
    Converts a choice into an XML element tree
    """
    return E.choice(choice.title, value=choice._value,)


def importXml(session, file_):
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

    # open the file if it's a filename
    if isinstance(file_, basestring):
        with codecs.open(file_, encoding='utf-8') as stream:
            tree = lxml.objectify.parse(stream)
    # otherwise assume it's an input stream
    else:
        tree = lxml.objectify.parse(file_)

    xschema = tree.getroot()
    schema = elementToSchema(xschema)

    try:
        session.add(schema)
        session.flush()
    except IntegrityError as e:
        if 'unique' in str(e):
            e = AlreadyExistsError(model.Schema, schema.name, schema.publish_date)
        raise e

    return schema


def elementToSchema(element):
    """
    Converts an objectified schema XML element to model ``Schema`` instance
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

    xattributes = element.find('attributes')

    if xattributes is not None:
        for index, xattribute in enumerate(xattributes.iterfind('attribute')):
            attribute = elementToAttribute(xattribute)
            attribute.order = index
            schema[attribute.name] = attribute

    return schema


def elementToAttribute(element):
    """
    Converts an objectified attribute XML element to model ``Attribute`` element
    """

    attribute = model.Attribute(
        name=str(element.attrib['name']),
        title=unicode(element.title),
        type=str(element.attrib['type']),
        )

    if 'required' in element.attrib:
        attribute.is_required = str(element.attrib['required']).lower()[0] in ('t', '1')

    if hasattr(element, 'description'):
        attribute.description = unicode(element.description)

    if hasattr(element, 'checksum'):
        attribute._checksum = str(element.checksum)

    if attribute.type == 'object':
        attribute.object_schema = elementToSchema(element.schema)

    if hasattr(element, 'collection'):
        attribute.is_collection = True
        if 'min' in element.collection.attrib:
            attribute.collection_min = int(element.collection.attrib['min'])
        if 'max' in element.collection.attrib:
            attribute.collection_max = int(element.collection.attrib['max'])

    if hasattr(element, 'limit'):
        if 'min' in element.limit.attrib:
            attribute.value_min = int(element.limit.attrib['min'])
        if 'max' in element.limit.attrib:
            attribute.value_max = int(element.limit.attrib['max'])

    if hasattr(element, 'validator'):
        attribute.validator = str(element.validator)

    xchoices = element.find('choices')

    if xchoices is not None:
        for index, xchoice in enumerate(xchoices.iterfind('choice')):
            choice = elementToChoice(xchoice)
            choice.order = index
            attribute.choices.append(choice)

    return attribute


def elementToChoice(element):
    """
    Converts an objectified choice XML element to model ``Choice`` instance
    """
    return model.Choice(
        title=unicode(element.text),
        _value=unicode(element.attrib['value']),
        )
