from collections import OrderedDict

from datetime import datetime
from pyramid.httpexceptions import \
    HTTPBadRequest, HTTPFound, HTTPForbidden, HTTPOk
from pyramid.session import check_csrf_token
from pyramid.view import view_config
import six
import sqlalchemy as sa
from sqlalchemy import orm
import wtforms
import wtforms.fields.html5
from zope.sqlalchemy import mark_changed

from occams.utils.forms import wtferrors, ModelField, Form
from occams_roster import generate
from occams_datastore import models as datastore
from occams_forms.renderers import \
    make_form, render_form, apply_data, entity_data, \
    form2json, modes

from .. import _, log, models
from . import (
    site as site_views,
    enrollment as enrollment_views,
    visit as visit_views,
    reference_type as reference_type_views,
    study as study_views,
    form as form_views)
from .external_service import render_url
from pyramid.response import Response
from pyramid.renderers import render
from occams_forms.renderers import \
    make_form, render_form, entity_data, \
    form2json, version2json, modes


#class SurveyLoginForm(wtforms.Form):
#        access_code = wtforms.PasswordField(
#            _(u'Access'),
#            validators=[
#                wtforms.validators.InputRequired(),
#                wtforms.validators.Length(max=128)
#                ]
#        )

@view_config(
    route_name='studies.survey',
    #permission='view',
    renderer='../templates/survey/login.pt')
def search_view(context, request):
    """
    """
    db_session = request.db_session
    url_key = request.matchdict.values()[0]
    if request.method == 'POST':# and form.validate():
        access_code = (request.POST['access_code'])
        survey_check = (
            db_session.query(models.Survey)
            .filter_by(url=url_key)
            .one()
        )
        if (access_code == survey_check.access_code):
            schema = (
                db_session.query(datastore.Entity)
                .filter_by(id=survey_check.entity_id)
                .one()
            )

            schema_id = schema.schema_id
            schema_name_query = (
                db_session.query(datastore.Schema)
                .filter_by(id=schema_id)
                .one()
            )

            allowed_schemata = (
                db_session.query(datastore.Schema)
                .join(models.study_schema_table)
                .join(models.Study)
                .join(models.Cycle)
                .filter(datastore.Schema.name == schema_name_query.name)
                #.filter(models.Cycle.id.in_([cycle.id for cycle in visit.cycles]))
                )
            allowed_versions = [s.publish_date for s in allowed_schemata]

            Form = make_form(
                db_session,
                schema_id,
                entity=survey_check.entity_id,
                show_metadata=True,
                transition=modes.ALL,
                allowed_versions=allowed_versions
            )

            form = Form(request.POST, data=entity_data(survey_check.entity_id))
            return {
                'form': render_form(
                    form,
                    attr={
                        'method': 'POST',
                        'action': request.current_route_path(),
                        'role': 'form'
                    }
                )
            }
        else:
            return 403

    else:
        return {

        }
