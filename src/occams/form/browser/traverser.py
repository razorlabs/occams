###############################################################################
##
## Copyright (c) 2006-2007 Zope Foundation and Contributors.
## All Rights Reserved.
##
## This software is subject to the provisions of the Zope Public License,
## Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
## THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
## WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
## WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
## FOR A PARTICULAR PURPOSE.
##
###############################################################################
#"""Base classes for Grok application components.
#
#When an application developer builds a Grok-based application, the
#classes they define each typically inherit from one of the base classes
#provided here.
#"""
#
#from five import grok
#
#from zope import component, interface
##from grokcore.rest import IRESTLayer
#from zope.publisher.interfaces.browser import IBrowserPublisher
#from zope.publisher.defaultview import getDefaultViewName
#from zope.publisher.interfaces import NotFound
##from grokcore.traverser.util import safely_locate_maybe
##from grokcore.traverser import traversable
#from zope.container.interfaces import IReadContainer
#from zope.publisher.interfaces.http import IHTTPRequest
#from grokcore.component.interfaces import IContext
#from zope.container.interfaces import IContainer
#
#from occams.form.interfaces import IRepository
#class Traverser(grok.MultiAdapter):
#    """Base class for traversers in Grok applications."""
#    grok.adapts(IRepository, IHTTPRequest)
#    grok.implements(IBrowserPublisher)
#
#    def __init__(self, context, request):
#        self.context = context
#        self.request = request
#
#    def browserDefault(self, request):
#        # if we have a RESTful request, we will handle
#        # GET, POST and HEAD differently (PUT and DELETE are handled already
#        # but not on the BrowserRequest layer but the HTTPRequest layer)
##        if IRESTLayer.providedBy(request):
##            rest_view = component.getMultiAdapter(
##                (self.context, self.request), name=request.method)
##            return rest_view, ()
#        view_name = getDefaultViewName(self.context, request)
#        view_uri = "@@%s" % view_name
#        return self.context, (view_uri,)
#
#    def publishTraverse(self, request, name):
#        subob = self.traverse(name)
##        if subob is not None:
##            return safely_locate_maybe(subob, self.context, name)
#
##        traversable_dict = traversable.bind().get(self.context)
##        if traversable_dict:
##            if name in traversable_dict:
##                subob = getattr(self.context, traversable_dict[name])
##                if callable(subob):
##                    subob = subob()
##                return safely_locate_maybe(subob, self.context, name)
#
#        # XXX Special logic here to deal with containers.  It would be
#        # good if we wouldn't have to do this here. One solution is to
#        # rip this out and make you subclass ContainerTraverser if you
#        # wanted to override the traversal behaviour of containers.
#        if IReadContainer.providedBy(self.context):
#            item = self.context.get(name)
#            if item is not None:
#                return item
#
#        view = component.queryMultiAdapter((self.context, request), name=name)
#        if view is not None:
#            return view
#
#        raise NotFound(self.context, name, request)
#
#    def traverse(self, name):
#        # this will be overridden by subclasses
#        pass
#
#
##class ContextTraverser(Traverser):
##    """Base class for context traversers in Grok applications.
##
##    A context traverser is like a normal `grok.Traverser` but, instead
##    of supplying its own `traverse()` method, it directs Grok to go call
##    the ``traverse()`` method on the context itself in order to process
##    the next name in the URL.
##
##    """
##    grok.adapts(IContext, IHTTPRequest)
##
##    def traverse(self, name):
##        traverse = getattr(self.context, 'traverse', None)
##        if traverse:
##            return traverse(name)
##
##
##class ContainerTraverser(Traverser):
##    """Base class for container traversers in Grok applications.
##
##    A container traverser is like a normal `grok.Traverser` but, instead
##    of supplying its own ``traverse()`` method, Grok will either call
##    the ``traverse()`` method on the context itself, if any, else call
##    ``get()`` on the container (a getitem-style lookup) in order to
##    resolve the next name in the URL.
##
##    """
##    grok.adapts(IContainer, IHTTPRequest)
##
##    def traverse(self, name):
##        traverse = getattr(self.context, 'traverse', None)
##        if traverse:
##            result = traverse(name)
##            if result is not None:
##                return result
##        # try to get the item from the container
##        return self.context.get(name)
