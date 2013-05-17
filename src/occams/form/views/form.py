import colander
import deform
import deform.widget
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import view_config
from pyramid_deform import CSRFSchema

from occams.datastore import model as datastore

from .. import Session


@view_config(
    route_name='form_list',
    renderer='occams.form:/templates/form/list.pt',
    layout='master_layout')
def list_(request):
    """ Lists all forms used by instance.
    """
    return {}
