"""
Form serialization tools to represent a form as a dictionary that can be 
persisted in a browser session or (hopefully at some point) in an annotation
storage of a content type in order to enable form change queues with
workflow-ie-ness and all that jazz.
"""

import zope.schema

from avrc.data.store import directives as datastore
from avrc.data.store.interfaces import typesVocabulary


def serializeForm(form):
    """
    Serializes a form as a top-level (master) form.
    """
    result = dict(
        name=form.getName(),
        title=datastore.title.bind().get(form),
        description=datastore.description.bind().get(form),
        version=datastore.version.bind().get(form),
        fields=dict()
        )

    for name, field in zope.schema.getFieldsInOrder(form):
        result['fields'][name] = serializeField(field)

    return result


def serializeField(field):
    """
    Serializes an individual field
    """
    type_ = datastore.type.bind().get(field) or typesVocabulary.getTerm(field.__class__).token

    result = dict(
        name=field.__name__,
        title=field.title,
        description=field.description,
        version=datastore.version.bind().get(field),
        type=type_,
        schema=None,
        choices=[],
        is_required=field.required,
        is_collection=isinstance(field, zope.schema.List),
        is_readonly=field.readonly,
        default=field.default,
        order=field.order,
        )

    if isinstance(field, zope.schema.Choice):
        for order, term in enumerate(field.vocabulary, start=0):
            result['choices'].append(dict(
                name=term.token,
                title=term.title,
                value=term.value,
                order=order,
                ))

    if isinstance(field, zope.schema.Object):
        result['schema'] = serializeForm(field.schema)

    return result
