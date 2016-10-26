import hashlib

from chameleon import PageTextTemplate
from slugify import slugify
from pyramid.httpexceptions import HTTPBadRequest, HTTPSeeOther
from pyramid.session import check_csrf_token
from pyramid.view import view_config
import wtforms

from occams.utils.forms import wtferrors, Form

from .. import _, models


@view_config(
    route_name='studies.study_external_services',
    permission='view',
    renderer='../templates/study/external-services.pt'
)
def view(context, request):
    """
    HTTP view of external services.

    This view will issue a GET request for a listing of current
    services created for the study.
    """

    return {'study': context.__parent__}


@view_config(
    route_name='studies.external_services',
    permission='view',
    xhr=True,
    renderer='json'
)
def list_(context, request):
    """
    Returns a listing of external service JSON records for the study
    """
    db_session = request.db_session
    study = context.__parent__

    query = (
        db_session.query(models.ExternalService)
        .filter_by(study=study)
        .order_by(models.ExternalService.title)
    )

    return {
        'external_services': [view_json(s, request) for s in query]
    }


@view_config(
    route_name='studies.external_service',
    permission='view',
    xhr=True,
    renderer='json'
)
def view_json(context, request):
    """
    Returns a single JSON record for the study's external service
    """
    return {
        '__url__': request.route_path(
            'studies.external_service',
            study=context.study.name,
            service=context.name
        ),
        'id': context.id,
        'name': context.name,
        'title': context.title,
        'description': context.description,
        'url_template': context.url_template,
    }


@view_config(
    route_name='studies.external_service',
    permission='delete',
    xhr=True,
    request_method='DELETE',
    renderer='json'
)
def delete_json(context, request):
    """
    Deletes an external service.

    If the record was successfully removed, the application will
    redirect to the listing.
    """
    check_csrf_token(request)
    db_session = request.db_session
    study = context.study
    service = context
    db_session.delete(service)
    db_session.flush()

    success_url = request.route_path(
        'studies.external_services',
        study=study.name,
    )

    return HTTPSeeOther(location=success_url)


@view_config(
    route_name='studies.external_services',
    permission='add',
    xhr=True,
    request_method='POST',
    renderer='json'
)
@view_config(
    route_name='studies.external_service',
    permission='edit',
    xhr=True,
    request_method='PUT',
    renderer='json'
)
def edit_json(context, request):
    """
    Adds/Edits a external service record.

    If the operation was successful, a redirect to the new record details
    will be returns. Otherwise a json record of validation errors will
    be returned.
    """
    check_csrf_token(request)
    db_session = request.db_session

    form = ExternalServiceForm(context, request).from_json(request.json_body)

    if not form.validate():
        return HTTPBadRequest(json={'errors': wtferrors(form)})

    if isinstance(context, models.ExternalServiceFactory):
        study = context.__parent__
        service = models.ExternalService(study=study)
    else:
        study = context.study
        service = context

    service.name = slugify(form.title.data)
    service.title = form.title.data
    service.description = form.description.data
    service.url_template = form.url_template.data
    db_session.flush()

    success_url = request.route_path(
        'studies.external_service',
        study=study.name,
        service=service.name
    )

    return HTTPSeeOther(location=success_url)


def render_url(url_template, raise_=True, fallback=None, **kw):

    def md5_callback(*args):
        return hashlib.md5(''.join(args)).hexdigest()

    fallback = fallback or '#malformed-url'

    template_parameters = dict.fromkeys(['pid', 'reference_number', 'md5'], '')
    template_parameters.update(kw)
    template_parameters['md5'] = md5_callback

    try:
        result = PageTextTemplate(url_template).render(**template_parameters)
    except:
        if raise_:
            raise
        else:
            return fallback

    return result


def ExternalServiceForm(context, request):
    db_session = request.db_session

    def check_unique(form, field):
        query = (
            db_session.query(models.ExternalService)
            .filter_by(name=slugify(field.data))
        )
        if isinstance(context, models.ExternalService):
            query = query.filter(models.ExternalService.id != context.id)
        (exists,) = db_session.query(query.exists()).one()
        if exists:
            raise wtforms.ValidationError(request.localizer.translate(_(
                u'Another external service with this name exists.')))

    def check_renders_correctly(form, field):
        try:
            render_url(field.data)
        except NameError as e:
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'Unsupported template variables: ${names}'),
                mapping={'names': e.message}))
        except Exception as e:
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'Unexpected erorr: ${message}'),
                mapping={'message': e.message}))

    class _ExternalServiceForm(Form):
        title = wtforms.StringField(
            validators=[
                wtforms.validators.input_required(),
                check_unique
            ])
        description = wtforms.TextField(
            validators=[wtforms.validators.optional()])
        url_template = wtforms.StringField(
            validators=[
                wtforms.validators.input_required(),
                check_renders_correctly
                ])

    return _ExternalServiceForm
