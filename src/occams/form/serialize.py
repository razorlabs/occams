"""
Form serialization tools to represent a form as a dictionary that can be
persisted in a browser session or (hopefully at some point) in an annotation
storage of a content type in order to enable form change queues with
workflow-ie-ness and all that jazz.
"""

import re

import zope.schema
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm

from avrc.data.store import directives as datastore
from avrc.data.store.interfaces import typesVocabulary


def serializeForm(form):
    """
    Serializes a form as a top-level (master) form.
    """
    fields = zope.schema.getFieldsInOrder(form)
    result = dict(
        name=form.getName(),
        title=datastore.title.bind().get(form),
        description=datastore.description.bind().get(form),
        version=datastore.version.bind().get(form),
        fields=dict([(n, serializeField(f)) for n, f in fields])
        )
    return result


def serializeField(field):
    """
    Serializes an individual field
    """
    type_ = datastore.type.bind().get(field) or typesVocabulary.getTerm(field.__class__).token

    result = dict(
        interface=field.interface.getName(),
        name=field.__name__,
        title=field.title,
        description=field.description,
        version=datastore.version.bind().get(field),
        type=type_,
        schema=None,
        choices=[],
        is_required=field.required,
        is_collection=isinstance(field, zope.schema.List),
        order=field.order,
        )

    vocabularyPart = getattr(field, 'value_type', field)

    if isinstance(vocabularyPart, zope.schema.Choice):
        for order, term in enumerate(vocabularyPart.vocabulary, start=0):
            result['choices'].append(dict(
                name=term.token,
                title=term.title,
                value=term.value,
                order=order,
                ))

    if isinstance(field, zope.schema.Object):
        result['schema'] = serializeForm(field.schema)

    return result


def tokenize(value):
    return re.sub('\W', '-', str(value).lower())


def moveField(formData, fieldName, position):
    changed = list()

    for field in sorted(formData['fields'].values(), key=lambda i: i['order']):
        # Move the field to here
        if position == field['order']:
            formData['fields'][fieldName]['order'] = position
            changed.append(fieldName)

        # Reorder anything following
        if field['name'] != fieldName and position >= field['order']:
            changed.append(fieldName)
            field['order'] += 1

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
