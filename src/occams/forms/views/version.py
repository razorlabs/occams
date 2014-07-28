from copy import deepcopy
import random
import json

import six
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest, HTTPForbidden
from pyramid.response import FileIter
from pyramid.view import view_config
from sqlalchemy import orm, sql
import wtforms
import wtforms.widgets.html5

from .. import _, models, Session


@view_config(
    route_name='version_view',
    renderer='../templates/version/view.pt',
    permission='form_view')
def view(request):
    schema = get_schema(**request.matchdict)
    return {'schema': schema}


@view_config(
    route_name='version_json',
    permission='form_view')
def view_json(request):
    schema = get_schema(**request.matchdict)
    fp = six.moves.cStringIO()
    json.dump(schema.to_json(), fp, indent=2)
    fp.seek(0)
    response = request.response
    response.content_type = 'application/json'
    response.content_disposition = 'attachment; filename="%s-%s.json"' % (
        schema.name, schema.publish_date.isoformat())
    response.app_iter = FileIter(fp)
    return response


@view_config(
    route_name='version_preview',
    renderer='../templates/version/preview.pt',
    permission='form_view')
def preview(request):
    """
    Preview form for test-drivining.
    """
    schema = get_schema(**request.matchdict)
    form = schema2wtf(schema)(request.POST)
    return {'schema': schema, 'form': form}


@view_config(
    route_name='version_edit',
    permission='form_edit',
    renderer='../templates/version/edit.pt')
def edit(request):
    from .field import FieldForm
    schema = get_schema(**request.matchdict)
    return {
        'schema': schema,
        'field_form': FieldForm(),
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


@view_config(
    route_name='version_view',
    xhr=True,
    check_csrf=True,
    request_method='POST',
    request_param='draft',
    permission='form_add',
    renderer='json')
def draft_json(request):
    """
    Drafts a new version of a published form.
    """
    schema = get_schema(**request.matchdict)
    if not schema.publish_date:
        raise HTTPBadRequest(json={
            'user_message': _(u'Cannot draft new from unpublished version')})
    draft = deepcopy(schema)
    Session.add(draft)
    Session.flush()
    request.session.flash(_(u'Successfully drafted new version'))
    return {
        # Hint the next resource to look for data
        '__next__': request.route_path('version_view',
                                       form=draft.name,
                                       version=draft.id)
    }


@view_config(
    route_name='version_view',
    xhr=True,
    check_csrf=True,
    request_method='DELETE',
    permission='form_delete',
    renderer='json')
def delete_json(request):
    """
    Edits form version metadata (not the fields)
    """
    schema = get_schema(**request.matchdict)

    if schema.publish_date is not None and not request.has_permission('admin'):
        raise HTTPForbidden(json={
            'user_message': _(u'Permission denied'),
            'debug_message': _(
                u'Non-administrators may not delete published forms')
        })

    Session.delete(schema)

    if schema.publish_date:
        request.session.flash(
            _(u'Successfully deleted %s version %s'
                % (schema.name, schema.publish_date)))
    else:
        request.session.flash(
            _(u'Successfully deleted draft of %s' % schema.name))

    return {
        # Hint the next resource to look for data
        '__next__': request.current_route_path(_route_name='form_list')
    }


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
    from .field import get_fields_data, types
    return {
        '__metadata__': {
            'types': types,
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


class VersionEditForm(wtforms.Form):

    name = wtforms.StringField(
        label=_('Schema Name'),
        description=_(
            u'The form\'s system name. '
            u'The name must not start with numbers or contain special '
            u'characters or spaces.'
            u'This name cannot be changed once the form is published.'))

    title = wtforms.StringField(
        label=_(u'Form Title'),
        description=_(
            u'The displayed name users will see when entering data.'),
        validators=[
            wtforms.validators.required(),
            wtforms.validators.Length(3, 128)])

    description = wtforms.TextAreaField(
        label=_(u'Form Description'),
        description=_(
            u'The human-readable description users will see at the '
            u'beginning of the form.'))

    publish_date = wtforms.DateField(
        label=_(u'Publish Date'))

    def validate_publish_date(form, field):
        if not field.publish_date:
            return

        version_exists = sql.exists().where(
            (models.Schema.name == field.data.lower())
            & (models.Schema.publish_date == field.publish_date))

        if not Session.query(version_exists).one():
            raise wtforms.validators.ValidationError(_(
                u'There is already a version for this publish date. '
                u'Please select a different publish date'))


def schema2wtf(schema):

    def make_field(attribute):
        kw = {
            'label': attribute.title,
            'description': attribute.description,
            'validators': []}

        if attribute.type == 'section':
            S = make_form(attribute.attributes)
            return wtforms.FormField(
                S, label=attribute.title, description=attribute.description)

        elif attribute.type == 'number':
            if attribute.decimal_places == 0:
                field_class = wtforms.IntegerField
                step = 1
            elif attribute.decimal_places is None:
                step = 'any'
                field_class = wtforms.DecimalField
            else:
                field_class = wtforms.DecimalField
                step = 1/float(pow(10, abs(attribute.decimal_places)))
            kw['widget'] = wtforms.widgets.html5.NumberInput(step)

        elif attribute.type == 'string':
            field_class = wtforms.StringField

        elif attribute.type == 'text':
            field_class = wtforms.TextAreaField

        elif attribute.type == 'date':
            field_class = wtforms.DateField

        elif attribute.type == 'datetime':
            field_class = wtforms.DateTimeField

        elif attribute.type == 'choice':
            choices = list(attribute.choices.values())
            if attribute.is_shuffled:
                choices = random.shuffle(choices)
            else:
                choices = sorted(choices, key=lambda c: c.order)
            kw['choices'] = [(c.name, c.title) for c in choices]
            if attribute.is_collection:
                field_class = wtforms.SelectMultipleField
                kw['widget'] = wtforms.widgets.ListWidget(prefix_label=False)
                kw['option_widget'] = wtforms.widgets.CheckboxInput()
            else:
                field_class = wtforms.SelectField
                kw['widget'] = wtforms.widgets.ListWidget(prefix_label=False)
                kw['option_widget'] = wtforms.widgets.RadioInput()

        elif attribute.type == 'blob':
            field_class = wtforms.FileField

        else:
            raise Exception(u'Unknown type: %s' % attribute.type)

        if attribute.is_required:
            kw['validators'].append(wtforms.validators.required())
        else:
            kw['validators'].append(wtforms.validators.optional())

        return field_class(**kw)

    def make_form(attributes):
        attributes = sorted(six.itervalues(attributes), key=lambda a: a.order)
        fields = dict([(a.name, make_field(a)) for a in attributes])
        return type('F', (wtforms.Form,), fields)

    return make_form(schema.attributes)
