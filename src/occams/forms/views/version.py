import six
from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config
from sqlalchemy import orm, sql
from wtforms import Form, validators, StringField, ValidationError
import wtforms
from wtforms.fields import html5
from wtforms.fields.html5 import DateField
from wtforms.widgets import TextArea

from .. import _, models, Session
from ..security import CSRF


def get_schema(form=None, version=None, **kw):
    """
    Helper method to retrieve the schema from a URL request
    """
    query = Session.query(models.Schema).filter_by(name=form)
    try:
        if version.isdigit():
            return query.filter_by(id=version).one()
        else:
            return query.filter_by(publish_date=version).one()
    except orm.exc.NoResultFound:
        raise HTTPNotFound


def get_version_data(request, schema):
    """
    Helper method to return schema version JSON data
    """
    # Avoid circular dependencies
    from .field import get_fields_data
    return {
        '__metadata__': {
            'types': [
                {'name': 'choice', 'title': _(u'Answer choices')},
                {'name': 'date', 'title': _(u'Date')},
                {'name': 'datetime', 'title': _(u'Date & Time')},
                {'name': 'blob', 'title': _(u'File Attachement')},
                {'name': 'number', 'title': _(u'Number')},
                {'name': 'section', 'title': _(u'Section')},
                {'name': 'string', 'title': _(u'Text')},
                {'name': 'text', 'title': _(u'Paragraph Text')}],
            'src': request.route_path(
                'version_view',
                form=schema.name,
                version=str(schema.publish_date or schema.id))},
        'id': schema.id,
        'name': schema.name,
        'title': schema.title,
        'description': schema.description,
        'publish_date': schema.publish_date and str(schema.publish_date),
        'retract_date': schema.retract_date and str(schema.retract_date),
        'fields': get_fields_data(request, schema)}


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


class VersionEditForm(Form):

    class Meta(object):
        csrf = True
        csrf_class = CSRF

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
    renderer='../templates/version/view.pt',
    permission='form_view')
def view(request):
    schema = get_schema(**request.matchdict)
    return {'schema': schema}


@view_config(
    route_name='version_preview',
    renderer='../templates/version/preview.pt',
    permission='form_view')
def preview(request):
    """
    Preview form for test-drivining.
    """
    schema = get_schema(**request.matchdict)
    SchemaForm = schema2wtf(schema)
    return {
        'schema': schema,
        'form': SchemaForm(),
    }


@view_config(
    route_name='version_edit',
    permission='form_edit',
    renderer='../templates/version/edit.pt')
def edit(request):
    from .field import FieldForm
    schema = get_schema(**request.matchdict)
    return {
        'schema': schema,
        'field_form': FieldForm(meta={'csrf_context': request.session})
    }


@view_config(
    route_name='version_edit',
    xhr=True,
    permission='form_edit',
    renderer='json')
@view_config(
    route_name='version_edit',
    request_param='alt=json',
    permission='form_edit',
    renderer='json')
def edit_json(request):
    """
    Edits form version metadata (not the fields)
    """
    schema = get_schema(**request.matchdict)
    return get_version_data(request, schema)

    #schema = get_schema(request)
    #edit_form = VersionEditForm(request.POST, schema)
    #if request.method == 'POST' and edit_form.validate():
        #edit_form.populate_obj(schema)
        #Session.flush()
        #return {
            #'type': 'alert',
            #'status': 'success',
            #'message': _(u'Changes saved')
        #}
    #return {
        #'type': 'form',
        #'title': _(u'Edit Form'),
        #'action': request.route_path('form_add'),
        #'method': 'POST',
        #'fields': [{
            #'label': f.label.text,
            #'description': f.description,
            #'required': f.flags.required,
            #'input_type': f.widget.input_type,
            #'input': f(class_='form-control'),
            #'value': f.data,
            #'errors': f.errors,
            #'order': i
            #} for i, f in enumerate(edit_form)],
        #'cancel': _(u'Cancel'),
        #'submit': _(u'Submit'),
    #}


class MultiCheckboxField(wtforms.SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = wtforms.widgets.ListWidget(prefix_label=False)
    option_widget = wtforms.widgets.CheckboxInput()


def schema2wtf(schema):

    def make_field(attribute):
        kw = {
            'label': attribute.title,
            'description': attribute.description,
            'validators': []
        }

        if attribute.type == 'integer':
            field_class = html5.IntegerField
        elif attribute.type == 'decimal':
            field_class = wtforms.DecimalField
        elif attribute.type == 'string':
            field_class = wtforms.StringField
        elif attribute.type == 'text':
            field_class = wtforms.TextAreaField
        elif attribute.type == 'date':
            field_class = wtforms.DateField
        elif attribute.type == 'datetime':
            field_class = wtforms.DateTimeField
        elif attribute.type == 'choice':
            kw['choices'] = [(c.name, c.title)
                             for c in sorted(six.itervalues(attribute.choices),
                                             key=lambda v: v.order)]
            if attribute.is_collection:
                field_class = MultiCheckboxField
            else:
                field_class = wtforms.RadioField
        elif attribute.type == 'blob':
            field_class = wtforms.FileField
        else:
            raise Exception(u'Unknown type: %s' % attribute.type)

        if attribute.is_required:
            kw['validators'].append(wtforms.validators.required())

        return field_class(**kw)

    F = type('F', (wtforms.Form,), {})

    # Non-fieldset fiels
    S = type('default', (wtforms.Form,), {})
    setattr(F, 'default', wtforms.FormField(S, label=u''))
    for attribute in sorted(six.itervalues(schema.attributes),
                            key=lambda v: v.order):
        if not attribute.section:
            setattr(S, attribute.name, make_field(attribute))

    # Fielset-fields
    for section in sorted(six.itervalues(schema.sections),
                          key=lambda v: v.order):
        S = type(str(section.name), (wtforms.Form,), {})
        setattr(F, section.name, wtforms.FormField(
            S,
            label=section.title,
            description=section.description,
        ))
        for attribute in sorted(six.itervalues(section.attributes),
                                key=lambda v: v.order):
            setattr(S, attribute.name, make_field(attribute))

    return F
