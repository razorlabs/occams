"""
Form serialization tools to represent a form as a dictionary that can be
persisted in a browser session or (hopefully at some point) in an annotation
storage of a content type in order to enable form change queues with
workflow-ie-ness and all that jazz.

NOTE
Some of the code in this file should probably be moved over to DatStore at
some point, such as the dictionary serializing and schema commit code. Maybe
once we start supporting SQL Alchemy objects natively (instead of interfaces)
this may be possible.
"""

import re

import zope.schema
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm
from occams.datastore.interfaces import typesVocabulary

# Copied from Python documentation
reservedWords = """
and     assert     break     class     continue
def     del     elif     else     except
exec     finally     for     from     global
if     import     in     is     lambda
not     or     pass     print     raise
return     try     while
Data     Float     Int     Numeric     Oxphys
array     close     float     int     input
open     range     type     write     zeros
acos     asin     atan     cos     e
exp     fabs     floor     log     log10
pi     sin     sqrt     tan
""".split()

def listFieldsets(schema_data):
    """
    Lists the fieldsets of a form
    """
    objectFilter = lambda x: bool(x['schema'])
    orderSort = lambda i: i['order']
    fields = schema_data['fields']
    objects = sorted(filter(objectFilter, fields.values()), key=orderSort)
    return [o['name'] for o in objects]

def serializeForm(form):
    """
    Serializes a form as a top-level (master) form.
    """
    result = dict(
        name=str(form.name),
        title=form.title,
        description=form.description,
        version=form.publish_date,
        fields=dict()
        )

    for name, field in form.items():
        result['fields'][name] = serializeField(field)
        result['fields'][name]['order'] = field.order

    return result


def serializeField(field):
    """
    Serializes an individual field
    """
    result = dict(
        name=str(field.name),
        title=field.title,
        description=field.description,
        type=field.type,
        schema=None,
        choices=[],
        is_required=field.is_required,
        is_collection=field.is_collection,
        order=field.order,
        )

    if len(field.choices):
        for choice in field.choices:
            result['choices'].append(dict(
                name=choice.name,
                title=choice.title,
                value=choice._value,
                order=choice.order,
                ))

    if field.type == 'object':
        result['schema'] = serializeForm(field.object_schema)

    return result


def tokenize(value):
    """
    Converts the value into a vocabulary token value
    """
    return re.sub('\W', '-', str(value).lower())


def camelize(value):
    """
    Converts the value into a valid camel case name
    Note: leaves the first word intact
    """
    result = ''
    for position, word in enumerate(re.split(r'\W+', value)):
        if position > 0:
            word = word[0].upper() + word[1:]
        result += word
    return symbolize(result)


def symbolize(value):
    """
    Converts the value into a valid Python variable name
    """
    # Remove invalid characters
    value = re.sub('[^0-9a-zA-Z_]', '', value)
    # Remove leading characters until we find a letter or underscore
    value = re.sub('^[^a-zA-Z_]+', '', value)
    return value


def cleanupChoices(data):
    # This is also similar to what is done in the edit form's apply
    # Do some extra work with choices on fields we didn't ask for.
    # Mostly things that are auto-generated for the user since it we
    # have never used and it they don't seem very relevant
    # (except, say, order)
    data.setdefault('choices', [])
    for order, choice in enumerate(data['choices'], start=0):
        if choice.get('value') is None:
            choice['value'] = choice['title']
        choice['name'] = tokenize(choice['value'])
        choice['order'] = order



def fieldFactory(fieldData):
    typeFactory = typesVocabulary.getTermByToken(fieldData['type']).value
    options = dict()

    if fieldData['choices']:
        terms = []
        for choice in sorted(fieldData['choices'], key=lambda c: c['order']):
            (token, title, value) = (choice['name'], choice['title'], choice['value'])
            term = SimpleTerm(token=str(token), title=title, value=value)
            terms.append(term)
        typeFactory = zope.schema.Choice
        options = dict(vocabulary=SimpleVocabulary(terms))

    if fieldData['is_collection']:
        # Wrap the typeFactory and options into the list
        options = dict(value_type=typeFactory(**options), unique=True)
        typeFactory = zope.schema.List

    # Update the options with the final fieldData parameters
    options.update(dict(
        __name__=str(fieldData['name']),
        title=fieldData['title'],
        description=fieldData['description'],
        required=fieldData['is_required'],
        ))

    result = typeFactory(**options)
    result.order = fieldData['order']
    return result
