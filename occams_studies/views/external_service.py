from slugify import slugify
from pyramid.httpexceptions import HTTPBadRequest, HTTPFound
from pyramid.session import check_csrf_token
from pyramid.view import view_config
import wtforms

from occams.utils.form import wtferrors, Form

from .. import _, models


@view_config(
    route_name='studies.external_services',
    permission='view',
    renderer='../templates/study/external-services.pt'
)
def view(context, request):
    return {}


@view_config(
    route_name='studies.external_services',
    permission='view',
    xhr=True,
    renderer='json'
)
def list_(context, request):
    """
    Renders the external services page
    """
    db_session = request.db_session

    query = (
        db_session(models.ExernalService)
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
    return {
        '__url_': request.current_route_path(),
        'id': context.id,
        'name': context.name,
        'title': context.title,
        'description': context.description,
        'url_template': context.url_template,
    }


@view_config(
    route_name='studies.external_services',
    permission='edit',
    xhr=True,
    method='POST',
    renderer='json'
)
@view_config(
    route_name='studies.external_service',
    permission='edit',
    xhr=True,
    method='PUT',
    renderer='json'
)
def edit_json(context, request):
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
    service.url_format = form.url_format.data
    db_session.flush()

    success_url = request.route_path(
        'studies.external_service',
        study=study.name,
        service=service.name
    )

    return HTTPFound(location=success_url)


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

    class _ExternalServiceForm(Form):
        title = wtforms.StringField(
            validators=[
                wtforms.validators.input_required(),
                check_unique
            ])
        description = wtforms.TextField(
            validators=[wtforms.validators.optional()])
        url_template = wtforms.StringField(
            validators=[wtforms.validators.input_required()])

    return _ExternalServiceForm
