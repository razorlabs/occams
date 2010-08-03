"""
This package contains all bootstrap classes that will be pre-loaded with
each data store.
"""

from zope.interface import Interface
import zope.schema

from plone.directives import form

states_vocabulary = zope.schema.SimpleVocabulary.fromValues(["ca", "wa"])

class ISubject(Interface):
    """
    """