from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config
from sqlalchemy import orm, sql
from wtforms import validators, StringField, ValidationError
from wtforms.fields.html5 import DateField
from wtforms.widgets import TextArea

from occams.form import _, models, Session
from occams.form.form import schema2wtf, CsrfForm


def get_schema(request):
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


def is_unique_publish_date(form, field):
    if not field.publish_date:
        return

    version_exists = sql.exists().where(
        (models.Schema.name == field.data.lower())
        & (models.Schema.publish_date == field.publish_date))

    if not Session.query(version_exists).one():
        raise ValidationError(_(
            u'There is already a version for this publish date. '
            u'Please select a different publish date'))


class VersionEditForm(CsrfForm):

    name = StringField(
        label=_('Schema Name'),
        description=_(
            u'The form\'s system name. '
            u'The name must not start with numbers or contain special '
            u'characters or spaces.'
            u'This name cannot be changed once the form is published.'))

    title = StringField(
        label=_(u'Form Title'),
        description=_(
            u'The displayed name users will see when entering data.'),
        validators=[
            validators.required(),
            validators.Length(3, 128)])

    description = StringField(
        label=_(u'Form Description'),
        description=_(
            u'The human-readable description users will see at the '
            u'beginning of the form.'),
        widget=TextArea())

    publish_date = DateField(
        label=_(u'Publish Date'),
        validators=[is_unique_publish_date])


@view_config(
    route_name='version_view',
    renderer='occams.form:templates/version/view.pt',
    permission='form_view')
def view(request):
    schema = get_schema(request)
    return {'schema': schema}


@view_config(
    route_name='version_preview',
    renderer='occams.form:templates/version/preview.pt',
    permission='form_view')
def preview(request):
    """
    Preview form for test-drivining.
    """
    schema = get_schema(request)
    SchemaForm = schema2wtf(schema)
    return {
        'schema': schema,
        'form': SchemaForm(),
    }


@view_config(
    route_name='version_edit',
    xhr=True,
    permission='form_edit')
def edit(request):
    """
    Edits form version metadata (not the fields)
    """
    schema = get_schema(request)
    edit_form = VersionEditForm(request.POST, schema)
    if request.method == 'POST' and edit_form.validate():
        edit_form.populate_obj(schema)
        Session.flush()
        return {
            'type': 'alert',
            'status': 'success',
            'message': _(u'Changes saved')
        }
    return {
        'type': 'form',
        'title': _(u'Edit Form'),
        'action': request.route_path('form_add'),
        'method': 'POST',
        'fields': [{
            'label': f.label.text,
            'description': f.description,
            'required': f.flags.required,
            'input_type': f.widget.input_type,
            'input': f(class_='form-control'),
            'value': f.data,
            'errors': f.errors,
            'order': i
            } for i, f in enumerate(edit_form)],
        'cancel': _(u'Cancel'),
        'submit': _(u'Submit'),
    }
