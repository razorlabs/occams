import datetime
import re

import colander
import deform
import deform.widget
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import view_config
from pyramid_deform import CSRFSchema
from pyramid_layout.panel import panel_config
from sqlalchemy import func, orm, sql

from occams.datastore import model as datastore

from .. import _, Session, Logger
from . import widgets


@view_config(
    route_name='version_view',
    renderer='occams.form:templates/version/view.pt',
    layout='web_layout')
def view(request):
    """
    """
    name = request.matchdict['form_name']
    version = request.matchdict['version']

    try:
        if isinstance(version, int):
            schema = Session.query(datastore.Schema).get(version)
        else:
            schema = query_version(Session, name, version).one()
    except ValueError, orm.exc.NoResultFound:
        raise HTTPNotFound

    layout = request.layout_manager.layout
    layout.content_title = schema.title
    return {}


def query_version(session, name, version):
    """
    """
    query = (
        session.query(datastore.Schema)
        .filter_by(name=name, publish_date=version))
    return query

