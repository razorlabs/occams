from pyramid.httpexceptions import HTTPOk
from .. import _


def jquery_wtform_validator(class_, context, request):
    """
    Reusable server-side validator for jquery validator requests.

    Parameters
        class_ -- a wtform class
        context -- request context
        request -- http request

    Returns an HTTP OK response with the JSON validation status:
        * true -- passed
        * string -- error message

    More info: http://jqueryvalidation.org/remote-method
    """
    field = request.GET.get('validate')
    if not field or not hasattr(class_, field):
        return HTTPOk(json=_(u'Unknown field: {field}',
                             mappings={'field': field}))
    form = class_.from_json({field: request.GET.get(field)})
    if not form.validate() and field in form.errors:
        # Send only the first error, jquery validation doesn't support lists
        return HTTPOk(json=form.errors[field][0])
    else:
        return HTTPOk(json=True)
