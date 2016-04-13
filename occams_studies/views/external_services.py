try:
    import unicodecsv as csv
except ImportError:  # pragma: nocover
    import csv
from datetime import date, timedelta

from slugify import slugify
from pyramid.events import subscriber, BeforeRender
from pyramid.httpexceptions import \
    HTTPBadRequest, HTTPForbidden, HTTPNotFound, HTTPOk
from pyramid.session import check_csrf_token
from pyramid.view import view_config
import sqlalchemy as sa
from sqlalchemy import orm
import wtforms
from wtforms.ext.dateutil.fields import DateField
from zope.sqlalchemy import mark_changed

from occams.utils.forms import Form, wtferrors, ModelField
from occams.utils.pagination import Pagination
from occams_datastore import models as datastore
from occams_forms.renderers import form2json, version2json

from .. import _, models
from . import cycle as cycle_views


@view_config(
    route_name='studies.external_services',
    permission='view',
    renderer='../templates/study/external-services.pt')
def external_services_view(context, request):
    """
    Renders the external services page
    """

    return {}
