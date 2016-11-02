# flake8: NOQA
# This module breaks my OCD-ness in favor of readability

from . import models


def includeme(config):
    """
    Helper method to configure available routes for the application
    """

    config.add_static_view(path='static', name='static', cache_max_age=3600)

    config.add_route('accounts.login',                      '/login')
    config.add_route('accounts.logout',                     '/logout')

    config.add_route('forms.index',                         '/forms',                                               factory=models.FormFactory)
    config.add_route('forms.version',                       '/forms/{form}/versions/{version}',                     factory=models.FormFactory, traverse='/{form}/versions/{version}')
    config.add_route('forms.version_editor',                '/forms/{form}/versions/{version}/editor',              factory=models.FormFactory, traverse='/{form}/versions/{version}')
    config.add_route('forms.version_preview',               '/forms/{form}/versions/{version}/preview',             factory=models.FormFactory, traverse='/{form}/versions/{version}')

    config.add_route('forms.fields',                        '/forms/{form}/versions/{version}/fields',              factory=models.FormFactory, traverse='/{form}/versions/{version}/fields')
    config.add_route('forms.field',                         '/forms/{form}/versions/{version}/fields/{field}',      factory=models.FormFactory, traverse='/{form}/versions/{version}/fields/{field}')

    config.add_route('forms.workflow',                      '/forms/workflows/default')

    config.add_route('studies.settings',                    '/studies/settings')

    config.add_route('studies.sites',                       '/studies/sites',                           factory=models.SiteFactory)
    config.add_route('studies.site',                        '/studies/sites/{site}',                    factory=models.SiteFactory, traverse='/{site}')

    config.add_route('studies.reference_types',             '/studies/reference_types',                 factory=models.ReferenceTypeFactory)
    config.add_route('studies.reference_type',              '/studies/reference_types/{reference_type}', factory=models.ReferenceTypeFactory, traverse='/{reference_type}')

    config.add_route('studies.exports',                     '/studies/exports',                         factory=models.ExportFactory)
    config.add_route('studies.exports_checkout',            '/studies/exports/checkout',                factory=models.ExportFactory)
    config.add_route('studies.exports_status',              '/studies/exports/status',                  factory=models.ExportFactory)
    config.add_route('studies.exports_notifications',       '/studies/exports/notifications',           factory=models.ExportFactory)
    config.add_route('studies.exports_faq',                 '/studies/exports/faq',                     factory=models.ExportFactory)
    config.add_route('studies.exports_codebook',            '/studies/exports/codebook',                factory=models.ExportFactory)
    config.add_route('studies.export',                      '/studies/exports/{export:\d+}',            factory=models.ExportFactory, traverse='/{export}')
    config.add_route('studies.export_download',             '/studies/exports/{export:\d+}/download',   factory=models.ExportFactory, traverse='/{export}')

    config.add_route('studies.patients',                    '/studies/patients',                        factory=models.PatientFactory)
    config.add_route('studies.patients_forms',              '/studies/patients/forms',                  factory=models.PatientFactory)
    config.add_route('studies.patient',                     '/studies/patients/{patient}',              factory=models.PatientFactory, traverse='/{patient}')
    config.add_route('studies.patient_forms',               '/studies/patients/{patient}/forms',        factory=models.PatientFactory, traverse='/{patient}/forms')
    config.add_route('studies.patient_form',                '/studies/patients/{patient}/forms/{form}', factory=models.PatientFactory, traverse='/{patient}/forms/{form}')

    config.add_route('studies.enrollments',                 '/studies/patients/{patient}/enrollments',                              factory=models.PatientFactory, traverse='/{patient}/enrollments')
    config.add_route('studies.enrollment',                  '/studies/patients/{patient}/enrollments/{enrollment}',                 factory=models.PatientFactory, traverse='/{patient}/enrollments/{enrollment}')
    config.add_route('studies.enrollment_termination',      '/studies/patients/{patient}/enrollments/{enrollment}/termination',     factory=models.PatientFactory, traverse='/{patient}/enrollments/{enrollment}')
    config.add_route('studies.enrollment_randomization',    '/studies/patients/{patient}/enrollments/{enrollment}/randomization',   factory=models.PatientFactory, traverse='/{patient}/enrollments/{enrollment}')

    config.add_route('studies.visits',                      '/studies/patients/{patient}/visits',                       factory=models.PatientFactory, traverse='/{patient}/visits')
    config.add_route('studies.visits_cycles',               '/studies/patients/{patient}/visits/cycles',                factory=models.PatientFactory, traverse='/{patient}/visits')
    config.add_route('studies.visit',                       '/studies/patients/{patient}/visits/{visit}',               factory=models.PatientFactory, traverse='/{patient}/visits/{visit}')

    config.add_route('studies.visit_forms',                 '/studies/patients/{patient}/visits/{visit}/forms',         factory=models.PatientFactory, traverse='/{patient}/visits/{visit}/forms')
    config.add_route('studies.visit_form',                  '/studies/patients/{patient}/visits/{visit}/forms/{form:\d+}',  factory=models.PatientFactory, traverse='/{patient}/visits/{visit}/forms/{form}')

    config.add_route('studies.index',                       '/',                                            factory=models.StudyFactory)
    config.add_route('studies.study',                       '/studies/{study}',                             factory=models.StudyFactory, traverse='/{study}')
    config.add_route('studies.study_schedule',              '/studies/{study}/schedule',                    factory=models.StudyFactory, traverse='/{study}')
    config.add_route('studies.study_external_services',     '/studies/{study}/manage-external-services',    factory=models.StudyFactory, traverse='/{study}')
    config.add_route('studies.study_enrollments',           '/studies/{study}/enrollments',                 factory=models.StudyFactory, traverse='/{study}')
    config.add_route('studies.study_visits',                '/studies/{study}/visits',                      factory=models.StudyFactory, traverse='/{study}')
    config.add_route('studies.study_visits_cycle',          '/studies/{study}/visits/{cycle}',              factory=models.StudyFactory, traverse='/{study}')
    config.add_route('studies.study_schemata',              '/studies/{study}/schemata',                    factory=models.StudyFactory, traverse='/{study}')
    config.add_route('studies.study_schema',                '/studies/{study}/schemata/{schema}',           factory=models.StudyFactory, traverse='/{study}')

    config.add_route('studies.cycles',                      '/studies/{study}/cycles',                      factory=models.StudyFactory, traverse='/{study}/cycles')
    config.add_route('studies.cycle',                       '/studies/{study}/cycles/{cycle}',              factory=models.StudyFactory, traverse='/{study}/cycles/{cycle}')
    config.add_route('studies.external_services',           '/studies/{study}/external-services',           factory=models.StudyFactory, traverse='/{study}/external-services')
    config.add_route('studies.external_service',            '/studies/{study}/external-services/{service}', factory=models.StudyFactory, traverse='/{study}/external-services/{service}')

    #survey routes
    config.add_route('studies.survey',                      '/survey/{survey}',                             factory=models.SurveyFactory, traverse='/{survey}')

