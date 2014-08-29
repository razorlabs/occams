from .. import models, Session


def list_(context, request):
    """
    Rertuns a list of sites that the user has access to
    """
    sites_query = Session.query(models.Site).order_by(models.Site.title)
    return {
        'sites': [
            s for s in sites_query if request.has_permission('site_view', s)],
        }
