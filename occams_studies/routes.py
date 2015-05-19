# flake8: NOQA
# This module breaks my OCD-ness in favor of readability
from datetime import datetime
from . import log

from . import models


def includeme(config):
    """
    Helper method to configure available routes for the application
    """

    config.add_static_view('/studies/static',               'occams_studies:static', cache_max_age=3600)

    config.add_route('socket.io',                           '/studies/socket.io/*remaining')

    config.add_route('studies.settings',                    '/studies/settings')

    config.add_route('studies.sites',                       '/studies/sites',                           factory=models.SiteFactory)
    config.add_route('studies.site',                        '/studies/sites/{site}',                    factory=models.SiteFactory, traverse='/{site}')

    config.add_route('studies.reference_types',             '/studies/reference_types',                 factory=models.ReferenceTypeFactory)
    config.add_route('studies.reference_type',              '/studies/reference_types/{reference_type}', factory=models.ReferenceTypeFactory, traverse='/{reference_type}')

    config.add_route('studies.exports',                     '/studies/exports',                         factory=models.ExportFactory)
    config.add_route('studies.exports_checkout',            '/studies/exports/checkout',                factory=models.ExportFactory)
    config.add_route('studies.exports_status',              '/studies/exports/status',                  factory=models.ExportFactory)
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
    config.add_route('studies.visit_form',                  '/studies/patients/{patient}/visits/{visit}/forms/{form}',  factory=models.PatientFactory, traverse='/{patient}/visits/{visit}/forms/{form}')


    config.add_route('studies.cycles',                      '/studies/{study}/cycles',          factory=models.StudyFactory, traverse='/{study}/cycles')
    config.add_route('studies.cycle',                       '/studies/{study}/cycles/{cycle}',  factory=models.StudyFactory, traverse='/{study}/cycles/{cycle}')

    config.add_route('studies.main',                        '/studies',                         factory=models.StudyFactory)
    config.add_route('studies.study',                       '/studies/{study}',                 factory=models.StudyFactory, traverse='/{study}')
    config.add_route('studies.study_schedule',              '/studies/{study}/schedule',        factory=models.StudyFactory, traverse='/{study}')
    config.add_route('studies.study_enrollments',           '/studies/{study}/enrollments',     factory=models.StudyFactory, traverse='/{study}')
    config.add_route('studies.study_visits',                '/studies/{study}/visits',          factory=models.StudyFactory, traverse='/{study}')
    config.add_route('studies.study_visits_cycle',          '/studies/{study}/visits/{cycle}',  factory=models.StudyFactory, traverse='/{study}')
    config.add_route('studies.study_schemata',              '/studies/{study}/schemata',        factory=models.StudyFactory, traverse='/{study}')
    config.add_route('studies.study_schema',                '/studies/{study}/schemata/{schema}', factory=models.StudyFactory, traverse='/{study}')

    log.debug('Routes configured')
