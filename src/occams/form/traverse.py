from zope.component import queryMultiAdapter
from zope.component import adapts
from zope.interface import implements

from grokcore.component.interfaces import IContext


from zope import component, interface
from zope.publisher.interfaces.browser import IBrowserPublisher
from zope.publisher.defaultview import getDefaultViewName
from zope.publisher.interfaces import NotFound
from zope.container.interfaces import IReadContainer
from zope.publisher.interfaces.http import IHTTPRequest
from grokcore.component.interfaces import IContext
from zope.container.interfaces import IContainer

import martian

import zope.location.location


def safely_locate_maybe(obj, parent, name):
    """Set an object's __parent__ (and __name__) if the object's
    __parent__ attribute doesn't exist yet or is None.

    If the object provides ILocation, __parent__ and __name__ will be
    set directly.  A location proxy will be returned otherwise.
    """

    if getattr(obj, '__parent__', None) is not None:
        return obj
    else:
        try:
            return zope.location.location.located(obj, parent, name)
        except TypeError:
            obj = obj.__of__(parent)
            return obj

from zope.interface import Interface

class Traverser(object):
    """Base class for traversers in Grok applications."""
    implements(IBrowserPublisher)

    martian.baseclass()

    def __init__(self, context, request):
#        super(Traverser, self).__init__(context, request)
        self.context = context
        self.request = request

    def browserDefault(self, request):
#        # if we have a RESTful request, we will handle
#        # GET, POST and HEAD differently (PUT and DELETE are handled already
#        # but not on the BrowserRequest layer but the HTTPRequest layer)
#        if IRESTLayer.providedBy(request):
#            rest_view = component.getMultiAdapter(
#                (self.context, self.request), name=request.method)
#            return rest_view, ()
        view_name = getDefaultViewName(self.context, request)
        view_uri = "@@%s" % view_name
        return self.context, (view_uri,)

    def publishTraverse(self, request, name):
        subob = self.traverse(name)
        if subob is not None:
            return safely_locate_maybe(subob, self.context, name)

#        traversable_dict = traversable.bind().get(self.context)
#        if traversable_dict:
#            if name in traversable_dict:
#                subob = getattr(self.context, traversable_dict[name])
#                if callable(subob):
#                    subob = subob()
#                return safely_locate_maybe(subob, self.context, name)

        # XXX Special logic here to deal with containers.  It would be
        # good if we wouldn't have to do this here. One solution is to
        # rip this out and make you subclass ContainerTraverser if you
        # wanted to override the traversal behaviour of containers.
        if IReadContainer.providedBy(self.context):
            item = self.context.get(name)
            if item is not None:
                return item

        view = component.queryMultiAdapter((self.context, request), name=name)
        if view is not None:
            return view

        raise NotFound(self.context, name, request)

    def traverse(self, name):
        # this will be overridden by subclasses
        pass

from zope.component import provideAdapter
import grokcore.component

class TraverserGrokker(martian.ClassGrokker):

    martian.component(Traverser)

    martian.directive(grokcore.component.context)

    def execute(self, factory, config, context, **kw):
        adapts = (context, IHTTPRequest)
        config.action(
            discriminator=('adapter', adapts, IBrowserPublisher, ''),
            callable=provideAdapter,
            args=(factory, adapts, IBrowserPublisher),
            )
        return True
