""" 
Specification of services provided by this plug-in.
"""

import zope.interface
import zope.schema

from hive.form import MessageFactory as _


class IFormSummary(zope.interface.Interface):
    """
    Form summary for listing purposes.
    """

    title = zope.schema.TextLine(
        title=_(u'Title'),
        description=_(u'Human-readable title'),
        readonly=True,
        )

    fieldCount = zope.schema.Int(
        title=_(u'# Fields'),
        description=_(
            u'Number of fields in the form, not including subform fields.'
            ),
        readonly=True,
        )

    revisionCount = zope.schema.Int(
        title=_(u'# Revisions'),
        description=_(u'Number of times the form has been revised'),
        readonly=True,
        )

    currentVersion = zope.schema.Date(
        title=_(u'Version'),
        description=_(u'Curent version number'),
        readonly=True,
        )

    createdOn = zope.schema.Date(
        title=_(u'Created'),
        description=_(u'The date the form was created'),
        readonly=True,
        )


class IRepository(zope.interface.Interface):
    """
    Form repository entry point.
    Objects of this type offer services for managing forms as well as
    form EAV tables from ``avrc.data.store.DataStore``
    """

    vendor = zope.schema.Choice(
        title=_(u'Database Vendor'),
        values=[None, 'mysql', 'postgresql', 'sqlite']
        )

    user = zope.schema.BytesLine(
        title=_(u'User'),
        description=_(
            u'A user with sufficient priviligies to access and '
            u'modify database content. The user must also have privileges '
            u'to create database tables. See vendor documentation for '
            u'proper user and privilege setup.'
            ),
        )

    password = zope.schema.Password(
        title=_(u'Password')
        )

    host = zope.schema.BytesLine(
        title=_(u'Host Name')
        )

    database = zope.schema.BytesLine(
        title=_(u'Database Name')
        )

