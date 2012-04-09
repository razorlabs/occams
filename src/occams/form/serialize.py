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
# from occams.datastore.model import Attribute
# from occams.datastore.model import Schema
# from occams.datastore.model import Choice
# from occams.datastore.model import NOW
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


# class CommitHelper(object):
#     """
#     Helper module for committing form changes to the database.
#     There are TONS of moving parts when committing form changes and so it was
#     decided to group them up into a class.
#     """

#     def __init__(self, session):
#         self.session = session

#     def __call__(self, data):
#         schema = self.doSchema(data)

#         attributeRetireCount = self.doRetireOldFields(data)
#         for field in data.get('fields', {}).values():
#             self.doAttribute(schema, field)
#         return schema

#     def doSchema(self, data):
#         """
#         Commits schema metadata
#         """
#         session = self.session
#         schema = (
#             session.query(Schema)
#             .filter((Schema.name == data['name']) & Schema.asOf(None))
#             .first()
#             )
#         changeable = ('name', 'title', 'description')

#         # version only if necessary
#         for setting in changeable:
#             isSettingModified = (schema is None) or \
#                  (getattr(schema, setting) != data[setting])

#             if isSettingModified:
#                 # retire old schema
#                 if schema:
#                     schema.remove_date = NOW
#                     session.flush()
#                 # add new schema
#                 schema = Schema(
#                     base_schema=getattr(schema, 'base_schema', None),
#                     name=data['name'],
#                     title=data['title'],
#                     description=data['description'],
#                     )
#                 session.add(schema)
#                 break
#         return schema

#     def doRetireOldFields(self, data):
#         """
#         Retires fields that are no longer part of the schema
#         """
#         session = self.session
#         retireCount = (
#             session.query(Attribute)
#             .filter(Attribute.schema.has(name=data['name']))
#             .filter(~Attribute.name.in_(data.get('fields', {}).keys()))
#             .update(dict(remove_date=NOW), 'fetch')
#             )
#         return retireCount

#     def doAttribute(self, schema, data):
#         """
#         Commits a single attribute metadata
#         This method is pretty lengthy as choices aren't currently versioned,
#         so we need to iterate through them and check if they have been
#         modified.
#         """
#         session = self.session
#         choices = dict()
#         attribute = (
#             session.query(Attribute)
#             .filter(Attribute.schema.has(name=schema.name))
#             .filter((Attribute.name == data['name']) & Attribute.asOf(None))
#             .first()
#             )

#         isChoicesModified = (attribute is None)
#         isSubFormModified = (attribute is None)

#         # Save subform changes first
#         if data['type'] == 'object':
#             object_schema = CommitHelper(session)(data['schema'])
#             if attribute is not None:
#                 isSubFormModified = (object_schema.id == attribute.object_schema.id)
#         else:
#             object_schema = None

#         # Convert choices to SQL Alchemy objects while checking if they've even
#         # been modified
#         for choiceData in data['choices']:
#             if isChoicesModified == False:
#                 # It's a new answer choiceData
#                 if choiceData['name'] not in attribute.choices:
#                     isChoicesModified = True
#                 # If it already exists, check if the settings have changed
#                 else:
#                     choice = attribute.choices[choiceData['name']]
#                     changeable = ('name', 'title', 'value', 'order')
#                     for setting in changeable:
#                         if getattr(choice, setting) != choiceData[setting]:
#                             isChoicesModified = True
#                             break

#             choices[choiceData['name']] = Choice(
#                 name=choiceData['name'],
#                 title=choiceData['title'],
#                 value=unicode(choiceData['value']),
#                 order=choiceData['order'],
#                 )

#         # Check if some have been removed
#         if attribute is not None:
#             for key in attribute.choices.keys():
#                 if key not in choices:
#                     isChoicesModified = True
#                     break

#         changeable = \
#             ('name', 'title', 'description', 'is_required', 'is_collection', 'order')

#         # Now check if attribute settings have been changed
#         for setting in changeable:
#             isSettingModified = (attribute is None) or \
#                 (getattr(attribute, setting) != data[setting])

#             if isChoicesModified or isSubFormModified or isSettingModified:
#                 # retire old schema
#                 if attribute:
#                     attribute.remove_date = NOW
#                     session.flush()

#                 attribute = Attribute(
#                     schema=schema,
#                     name=data['name'],
#                     title=data['title'],
#                     description=data['description'],
#                     type=data['type'],
#                     object_schema=object_schema,
#                     choices=choices,
#                     order=data['order'],
#                     # These properties don't apply to all types, so set
#                     # them conditionally
#                     is_required=data.get('is_required'),
#                     is_collection=data.get('is_collection'),
#                     is_inline_object=(data['type'] == 'object' or None),
#                     )

#                 session.add(attribute)
#                 break

#         return attribute


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
        # version=field.publish_date,
        type=field.type,
        schema=None,
        choices=[],
        is_required=field.is_required,
        is_collection=field.is_collection,
        order=field.order,
        )

    #vocabularyPart = getattr(field, 'value_type', field)

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


def moveField(form, field, after=None):
    changed = list()
    if after is None:
        field.order = 0
    else:
        field.order = form[after].order + 1
    # Move everything that follows
    for formfield in sorted(form.values(), key=lambda i: i.order):
        if formfield != field and formfield.order >= field.order:
            formfield.order += 1
    ## ok, we need to reorder everything, because we're "adding" an item
    order = 0
    for formfield in sorted(form.values(), key=lambda i: i.order):
        oldOrder = formfield.order
        formfield.order = order
        if order != oldOrder:
            changed.append(formfield)
        order +=1
    return changed


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
