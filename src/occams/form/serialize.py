"""
Form serialization tools to represent a form as a dictionary that can be
persisted in a browser session or (hopefully at some point) in an annotation
storage of a content type in order to enable form change queues with
workflow-ie-ness and all that jazz.
"""

import re

from collective.beaker.interfaces import ISession
from zope.globalrequest import getRequest
import zope.schema
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm

from avrc.data.store import directives as datastore
from avrc.data.store.model import Attribute
from avrc.data.store.model import Schema
from avrc.data.store.model import Choice
from avrc.data.store.model import NOW
from avrc.data.store.interfaces import IDataStore
from avrc.data.store.interfaces import typesVocabulary
from occams.form.interfaces import DATA_KEY


class Workspace(object):
    """
    Helper method for keeping track of form changes
    """

    def __init__(self, repository):
        self.repository = repository
        self.browserSession = ISession(getRequest())
        self.browserSession.setdefault(DATA_KEY, {})
        self.data = self.browserSession[DATA_KEY]

    def save(self):
        """
        Saves the current workspace (nothing done to database)
        """
        self.browserSession.save()

    def load(self, name):
        """
        Loads a serialized form from the workspace or from datastore
        """
        try:
            formData = self.data[name]
        except KeyError:
            import pdb; pdb.set_trace()
            form = IDataStore(self.repository).schemata.get(name)
            formData = serializeForm(form)
            self.data[name] = formData
            self.save()
        return formData

    def __contains__(self, key):
        return key in self.data

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, item):
        self.data[key] = item

    def clear(self, name):
        """
        Cancels changes done to a form
        """
        try:
            del self.data[name]
            self.save()
        except KeyError:
            pass

    def commit(self, name):
        """
        Commits the item in the workspace to the database
        """
        session = IDataStore(self.repository).session

        def commitFormHelper(data):
            oldSchema = (
                session.query(Schema)
                .filter((Schema.name == data['name']) & Schema.asOf(None))
                .first()
                )

            # add new schema
            newSchema = Schema(
                name=data['name'],
                title=data['title'],
                description=data['description'],
                )

            session.add(newSchema)

            # retire old schema
            if oldSchema:
                oldSchema.remove_date = NOW
                newSchema.base_schema = oldSchema.base_schema

            # retire old fields
            schemaRetireCount = (
                session.query(Attribute)
                .filter(Attribute.schema.has(name=newSchema.name))
                .filter(~Attribute.name.in_(data.get('fields', {}).keys()))
                .update(dict(remove_date=NOW), 'fetch')
                )

            # save fields
            for field in data.get('fields', {}).values():
                # retire old newAttribute
                attributeRetireCount = (
                    session.query(Attribute)
                    .filter(Attribute.schema.has(name=newSchema.name))
                    .filter((Attribute.name == field['name']) & Attribute.asOf(None))
                    .update(dict(remove_date=NOW), 'fetch')
                    )

                # save new newAttribute
                newAttribute = Attribute(
                    schema=newSchema,
                    name=field['name'],
                    title=field['title'],
                    description=field['description'],
                    type=field['type'],
                    object_schema=field['schema'] and commitFormHelper(field['schema']) or None,
                    is_required=field['is_required'],
                    is_collection=field['is_collection'],
                    order=field['order'],
                    )

                # save new choices
                for choice in field['choices']:
                    newChoice = Choice(
                        attribute=newAttribute,
                        name=choice['name'],
                        title=choice['title'],
                        value=unicode(choice['value']),
                        order=choice['order'],
                        )

            return newSchema

        schema = commitFormHelper(self.data.get(name, {}))
        self.clear(name)


def listFieldsets(repository, formName):
    """
    Lists the fieldsets of a form
    """
    request = getRequest()
    objectFilter = lambda x: bool(x['schema'])
    orderSort = lambda i: i['order']
    fields = ISession(request)[DATA_KEY][formName]['fields']
    objects = sorted(filter(objectFilter, fields.values()), key=orderSort)
    return [o['name'] for o in objects]


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
        fields=dict()
        )

    for order, field in enumerate(fields, start=0):
        (name, field) = field
        result['fields'][name] = serializeField(field)
        result['fields'][name]['order'] = order

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
