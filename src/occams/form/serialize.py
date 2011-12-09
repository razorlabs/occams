"""
Form serialization tools to represent a form as a dictionary that can be 
persisted in a browser session or (hopefully at some point) in an annotation
storage of a content type in order to enable form change queues with
workflow-ie-ness and all that jazz.

The structure is as follows::

    dict(
        name=FORM_NAME,
        title=FORM_DESCRIPTION,
        version=FORM_VERSION,
        groups=dict(
            FIELDSET_NAME=dict(
                name=FIELDSET_NAME,
                schema=OBJECT_SCHEMA_NAME,
                title=FIELDSET_TITLE,
                description=FIELDSET_DESCRIPTION,
                version=FIELDSET_VERSION,
                order=FIELDSET_ORDER,
                fields=dict(
                    name=FIELD_NAME,
                    title=FIELD_TITLE,
                    description=FIELD_DESCRIPTION,
                    version=FIELD_VERSION,
                    type=FIELD_TYPE,
                    choices=dict(
                        name=CHOICE_NAME,
                        title=CHOICE_TITLE,
                        value=CHOICE_VALUE,
                        order=CHOICE_ORDER,
                        ),
                    is_required=FIELD_IS_REQUIRED,
                    is_collection=FIELD_IS_COLLECTION,
                    is_readonly=FIELD_IS_READONLY,
                    default=FIELD_DEFAULT,
                    order=FIELD_ORDER,
                    )
                )
            )
    )

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
        groups=dict()
        )

    defaultNames = []

    for name, field in zope.schema.getFieldsInOrder(form):
        if isinstance(field, zope.schema.Object):
            result['groups'][name] = serializeFieldSet(field.schema, for_=field)
        else:
            defaultNames.append(name)

    # top-level form fields are treated as the "default" fieldset
    result['groups'][None] = serializeFieldSet(form, fields=defaultNames)

    return result


def serializeFieldSet(form, fields=None, for_=None):
    """
    Serializes a form as a sub-form (fieldset)
    """
    if fields is None:
        fields = zope.schema.getFieldNames(form)

    result = dict(
        name=(for_ and for_.__name__ or None),
        schema=form.getName(),
        title=(for_ and datastore.title.bind().get(for_) or None),
        description=(for_ and datastore.description.bind().get(for_) or None),
        version=(for_ and datastore.version.bind().get(for_) or None),
        order=(for_ and for_.order or None),
        fields=dict([(name, serializeField(form[name])) for name in fields]),
        )

    return result


def serializeField(field):
    """
    Serializes an individual field
    """
    type_ = datastore.type.bind().get(field)
    if type_ is None:
        type_ = typesVocabulary.getTerm(field.__class__).token

    result = dict(
                name=field.__name__,
                title=field.title,
                description=field.description,
                version=datastore.version.bind().get(field),
                type=type_,
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

    return result
