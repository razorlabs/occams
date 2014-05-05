from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config
from sqlalchemy import orm

from occams.form import models, Session
from occams.form.form import schema2wtf


def get_form(request):
    """
    Helper method to retrieve the schema from a URL request
    """
    name = request.matchdict['form']
    version = request.matchdict['version']
    query = Session.query(models.Schema).filter_by(name=name)

    if version.isdigit():
        query = query.filter_by(id=version)
    else:
        query = query.filter_by(publish_date=version)

    try:
        return query.one()
    except orm.exc.NoResultFound:
        raise HTTPNotFound


@view_config(
    route_name='version_view',
    renderer='occams.form:templates/version/view.pt',
    permission='form_view')
def view(request):
    """
    Overview of the form version
    """
    schema = get_form(request)

    return {'schema': schema}


@view_config(
    route_name='version_codebook',
    renderer='occams.form:templates/version/codebook.pt',
    permission='form_view')
def codebook(request):
    """
    Codebook Page
    """
    schema = get_form(request)
    return {'schema': schema}


@view_config(
    route_name='version_preview',
    renderer='occams.form:templates/version/preview.pt',
    permission='form_view')
def preview(request):
    """
    Preview form for test-drivining.
    """
    schema = get_form(request)
    SchemaForm = schema2wtf(schema)
    return {
        'schema': schema,
        'form': SchemaForm(),
    }


@view_config(
    route_name='version_edit',
    renderer='occams.form:templates/version/edit.pt',
    permission='form_edit')
def edit(request):
    """
    Editor Page
    """
    schema = get_form(request)
    return {'schema': schema}
