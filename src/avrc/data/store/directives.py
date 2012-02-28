"""
Some of the code for directives was adopted from plone.directives.form

TODO:
    * Need to add scope constraints, currently the directives can
        be applied to anything...

    * Resource/Table directives
        * Ideas:
            * url: The url to the Resource
            * primary: The table's primary key
"""

import martian
import zope.schema
from zope.interface import Interface
from zope.interface.interface import TAGGED_DATA


DATASTORE_KEY = '__avrc_data_store__'

# Allowed type constraints for choices
CASTS = ['string', 'decimal', 'integer', 'boolean']


class Table(object):
    """
    A Schema type that is stored in a SQL database table.
    Classes that subclass this marker will be recognized by datastore
    but will have their data stored in a conventional SQL table.
    """


class Resource(Interface):
    """
    A Schema type that is stored in an external resource.
    (e.g. Zope content type, MedLine resource, etc)
    Interfaces that subclass this marker are responsible for defining
    how to access the resource (e.g. via URL)
    """


class Schema(Interface):
    """
    Marker interfaces for DataStore schemata.
    Interfaces that subclass this marker will be able to be stored in
    to datastore's EAV storage structure.
    """


class MetaDataValueStorage(object):
    """
    Stores annotations in in the Interface's ``TAGGED_DATA``
    """

    def set(self, locals_, directive, value):
        tags = locals_.setdefault(TAGGED_DATA, {}).setdefault(directive.key, {})
        tags[directive.dotted_name()] = value


    def get(self, directive, component, default):
        key = directive.dotted_name()
        return component.queryTaggedValue(directive.key, {}).get(key, default)


    def setattr(self, context, directive, value):
        directive.validate(value)
        tags = context.queryTaggedValue(directive.key)

        if tags is None:
            tags = dict()
            context.setTaggedValue(directive.key, tags)

        tags[directive.dotted_name()] = value


STORE_VALUE = MetaDataValueStorage()

#
# General directives
#

class __id__(martian.Directive):
    """
    The database ID number of the item.
    This directive is only intended to be read-only by client libraries.
    Intended scope: Schema/Field
    """
    scope = martian.CLASS
    key = DATASTORE_KEY
    store = STORE_VALUE
    validate = zope.schema.Int(required=False).validate


class version(martian.Directive):
    """
    The version of the item.
    The date the item came into existence is the version value.
    Intended scope: Schema/Field
    """
    scope = martian.CLASS
    key = DATASTORE_KEY
    store = STORE_VALUE
    validate = zope.schema.Datetime(required=False).validate


class inline(martian.Directive):
    """
    If set, the schema (or field referencing the schema) is rendered inline.
    Intended scope: Schema/Field
    """
    scope = martian.CLASS
    key = DATASTORE_KEY
    store = STORE_VALUE
    validate = zope.schema.Bool(required=False).validate

#
# Schema-only directives
#

class title(martian.Directive):
    """
    The title of the item.
    Intended scope: Schema
    """
    scope = martian.CLASS
    key = DATASTORE_KEY
    store = STORE_VALUE
    validate = zope.schema.TextLine(required=True).validate


class description(martian.Directive):
    """
    The description of the item.
    Intended scope: Schema
    """
    scope = martian.CLASS
    key = DATASTORE_KEY
    store = STORE_VALUE
    validate = zope.schema.Text(required=False).validate

#
# Field-only directives
#


class type(martian.Directive):
    """
    Enforces an EAV type on the field.
    Intended scope: Field
    """
    scope = martian.CLASS
    key = DATASTORE_KEY
    store = STORE_VALUE
    validate = zope.schema.Choice(required=False, values=CASTS).validate
