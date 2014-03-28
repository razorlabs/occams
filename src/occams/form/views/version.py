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

from occams.form import _, Session, log, widgets
from occams.datastore import models as datastore


#@view_config(
    #route_name='version_view',
    #renderer='occams.form:templates/version/view.pt',
    #layout='web_layout')
#def view(request):
    #"""
    #"""
    #name = request.matchdict['form_name']
    #version = request.matchdict['version']

    #try:
        #schema = get_version(Session, name, version)
    #except ValueError, orm.exc.NoResultFound:
        #raise HTTPNotFound

    #form = Form(schema=schema)

    #layout = request.layout_manager.layout
    #layout.content_title = schema.title
    #return {'form': form.render()}


#def get_version(session, name, version):
    #query = session.query(datastore.Schema)
    #if isinstance(version, int):
        #return query.filter_by(id=version).one()
    #return query.filter_by(name=name, publish_date=version).one()

