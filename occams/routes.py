# flake8: NOQA
# This module breaks my OCD-ness in favor of readability

from . import models


def includeme(config):
    """
    Helper method to configure available routes for the application
    """

    config.add_static_view(path='static', name='static', cache_max_age=3600)

    config.add_route('accounts.login',                      r'/login')
    config.add_route('accounts.logout',                     r'/logout')

    config.add_route('forms.index',                         r'/forms',                                               factory=models.FormFactory)
    config.add_route('forms.version',                       r'/forms/{form}/versions/{version}',                     factory=models.FormFactory, traverse='/{form}/versions/{version}')
    config.add_route('forms.version_editor',                r'/forms/{form}/versions/{version}/editor',              factory=models.FormFactory, traverse='/{form}/versions/{version}')
    config.add_route('forms.version_preview',               r'/forms/{form}/versions/{version}/preview',             factory=models.FormFactory, traverse='/{form}/versions/{version}')

    config.add_route('forms.fields',                        r'/forms/{form}/versions/{version}/fields',              factory=models.FormFactory, traverse='/{form}/versions/{version}/fields')
    config.add_route('forms.field',                         r'/forms/{form}/versions/{version}/fields/{field}',      factory=models.FormFactory, traverse='/{form}/versions/{version}/fields/{field}')

    config.add_route('studies.settings',                    r'/studies/settings')

    config.add_route('studies.sites',                       r'/studies/sites',                           factory=models.SiteFactory)
    config.add_route('studies.site',                        r'/studies/sites/{site}',                    factory=models.SiteFactory, traverse='/{site}')

    config.add_route('studies.reference_types',             r'/studies/reference_types',                 factory=models.ReferenceTypeFactory)
    config.add_route('studies.reference_type',              r'/studies/reference_types/{reference_type}', factory=models.ReferenceTypeFactory, traverse='/{reference_type}')

    config.add_route('studies.exports',                     r'/studies/exports',                         factory=models.ExportFactory)
    config.add_route('studies.exports_checkout',            r'/studies/exports/checkout',                factory=models.ExportFactory)
    config.add_route('studies.exports_status',              r'/studies/exports/status',                  factory=models.ExportFactory)
    config.add_route('studies.exports_notifications',       r'/studies/exports/notifications',           factory=models.ExportFactory)
    config.add_route('studies.exports_faq',                 r'/studies/exports/faq',                     factory=models.ExportFactory)
    config.add_route('studies.exports_codebook',            r'/studies/exports/codebook',                factory=models.ExportFactory)
    config.add_route('studies.export',                      r'/studies/exports/{export:\d+}',            factory=models.ExportFactory, traverse='/{export}')
    config.add_route('studies.export_download',             r'/studies/exports/{export:\d+}/download',   factory=models.ExportFactory, traverse='/{export}')

    config.add_route('studies.patients',                    r'/studies/patients',                        factory=models.PatientFactory)
    config.add_route('studies.patients_forms',              r'/studies/patients/forms',                  factory=models.PatientFactory)
    config.add_route('studies.patient',                     r'/studies/patients/{patient}',              factory=models.PatientFactory, traverse='/{patient}')
    config.add_route('studies.patient_forms',               r'/studies/patients/{patient}/forms',        factory=models.PatientFactory, traverse='/{patient}/forms')
    config.add_route('studies.patient_form',                r'/studies/patients/{patient}/forms/{form}', factory=models.PatientFactory, traverse='/{patient}/forms/{form}')

    config.add_route('studies.enrollments',                 r'/studies/patients/{patient}/enrollments',                              factory=models.PatientFactory, traverse='/{patient}/enrollments')
    config.add_route('studies.enrollment',                  r'/studies/patients/{patient}/enrollments/{enrollment}',                 factory=models.PatientFactory, traverse='/{patient}/enrollments/{enrollment}')
    config.add_route('studies.enrollment_termination',      r'/studies/patients/{patient}/enrollments/{enrollment}/termination',     factory=models.PatientFactory, traverse='/{patient}/enrollments/{enrollment}')
    config.add_route('studies.enrollment_randomization',    r'/studies/patients/{patient}/enrollments/{enrollment}/randomization',   factory=models.PatientFactory, traverse='/{patient}/enrollments/{enrollment}')

    config.add_route('studies.visits',                      r'/studies/patients/{patient}/visits',                       factory=models.PatientFactory, traverse='/{patient}/visits')
    config.add_route('studies.visits_cycles',               r'/studies/patients/{patient}/visits/cycles',                factory=models.PatientFactory, traverse='/{patient}/visits')
    config.add_route('studies.visit',                       r'/studies/patients/{patient}/visits/{visit}',               factory=models.PatientFactory, traverse='/{patient}/visits/{visit}')

    config.add_route('studies.visit_forms',                 r'/studies/patients/{patient}/visits/{visit}/forms',         factory=models.PatientFactory, traverse='/{patient}/visits/{visit}/forms')
    config.add_route('studies.visit_form',                  r'/studies/patients/{patient}/visits/{visit}/forms/{form:\d+}',  factory=models.PatientFactory, traverse='/{patient}/visits/{visit}/forms/{form}')

    config.add_route('studies.index',                       r'/',                                            factory=models.StudyFactory)
    config.add_route('studies.study',                       r'/studies/{study}',                             factory=models.StudyFactory, traverse='/{study}')
    config.add_route('studies.study_schedule',              r'/studies/{study}/schedule',                    factory=models.StudyFactory, traverse='/{study}')
    config.add_route('studies.study_external_services',     r'/studies/{study}/manage-external-services',    factory=models.StudyFactory, traverse='/{study}')
    config.add_route('studies.study_enrollments',           r'/studies/{study}/enrollments',                 factory=models.StudyFactory, traverse='/{study}')
    config.add_route('studies.study_visits',                r'/studies/{study}/visits',                      factory=models.StudyFactory, traverse='/{study}')
    config.add_route('studies.study_visits_cycle',          r'/studies/{study}/visits/{cycle}',              factory=models.StudyFactory, traverse='/{study}')
    config.add_route('studies.study_schemata',              r'/studies/{study}/schemata',                    factory=models.StudyFactory, traverse='/{study}')
    config.add_route('studies.study_schema',                r'/studies/{study}/schemata/{schema}',           factory=models.StudyFactory, traverse='/{study}')

    config.add_route('studies.cycles',                      r'/studies/{study}/cycles',                      factory=models.StudyFactory, traverse='/{study}/cycles')
    config.add_route('studies.cycle',                       r'/studies/{study}/cycles/{cycle}',              factory=models.StudyFactory, traverse='/{study}/cycles/{cycle}')
    config.add_route('studies.external_services',           r'/studies/{study}/external-services',           factory=models.StudyFactory, traverse='/{study}/external-services')
    config.add_route('studies.external_service',            r'/studies/{study}/external-services/{service}', factory=models.StudyFactory, traverse='/{study}/external-services/{service}')

    #survey routes
    config.add_route('studies.survey',                      r'/survey/{survey}',                             factory=models.SurveyFactory, traverse='/{survey}')

