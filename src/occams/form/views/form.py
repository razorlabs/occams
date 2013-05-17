import colander
import deform
import deform.widget
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import view_config, view_defaults
from pyramid_deform import CSRFSchema
from pyramid_layout.layout import layout_config
from pyramid_layout.panel import panel_config

from occams.datastore import model as datastore

from .. import Session


@view_config(
        route_name='form_list',
        renderer='occams.form:/templates/form/list.pt')
def list_(request):
    """ Lists all forms used by instance.
    """
    return {}
