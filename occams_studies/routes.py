# flake8: NOQA
# This module breaks my OCD-ness in favor of readability
from datetime import datetime
from . import log

from . import models


def includeme(config):
    """
    Helper method to configure available routes for the application
    """

    config.add_static_view(path='occams_studies:static',    name='/static', cache_max_age=3600)

    config.add_route('studies.settings',                    '/settings')

    config.add_route('studies.sites',                       '/sites',                           factory=models.SiteFactory)
    config.add_route('studies.site',                        '/sites/{site}',                    factory=models.SiteFactory, traverse='/{site}')

    config.add_route('studies.reference_types',             '/reference_types',                 factory=models.ReferenceTypeFactory)
    config.add_route('studies.reference_type',              '/reference_types/{reference_type}', factory=models.ReferenceTypeFactory, traverse='/{reference_type}')

    config.add_route('studies.exports',                     '/exports',                         factory=models.ExportFactory)
    config.add_route('studies.exports_checkout',            '/exports/checkout',                factory=models.ExportFactory)
    config.add_route('studies.exports_status',              '/exports/status',                  factory=models.ExportFactory)
    config.add_route('studies.exports_notifications',       '/exports/notifications',           factory=models.ExportFactory)
    config.add_route('studies.exports_faq',                 '/exports/faq',                     factory=models.ExportFactory)
    config.add_route('studies.exports_codebook',            '/exports/codebook',                factory=models.ExportFactory)
    config.add_route('studies.export',                      '/exports/{export:\d+}',            factory=models.ExportFactory, traverse='/{export}')
    config.add_route('studies.export_download',             '/exports/{export:\d+}/download',   factory=models.ExportFactory, traverse='/{export}')

    config.add_route('studies.patients',                    '/patients',                        factory=models.PatientFactory)
    config.add_route('studies.patients_forms',              '/patients/forms',                  factory=models.PatientFactory)
    config.add_route('studies.patient',                     '/patients/{patient}',              factory=models.PatientFactory, traverse='/{patient}')
    config.add_route('studies.patient_forms',               '/patients/{patient}/forms',        factory=models.PatientFactory, traverse='/{patient}/forms')
    config.add_route('studies.patient_form',                '/patients/{patient}/forms/{form}', factory=models.PatientFactory, traverse='/{patient}/forms/{form}')

    config.add_route('studies.enrollments',                 '/patients/{patient}/enrollments',                              factory=models.PatientFactory, traverse='/{patient}/enrollments')
    config.add_route('studies.enrollment',                  '/patients/{patient}/enrollments/{enrollment}',                 factory=models.PatientFactory, traverse='/{patient}/enrollments/{enrollment}')
    config.add_route('studies.enrollment_termination',      '/patients/{patient}/enrollments/{enrollment}/termination',     factory=models.PatientFactory, traverse='/{patient}/enrollments/{enrollment}')
    config.add_route('studies.enrollment_randomization',    '/patients/{patient}/enrollments/{enrollment}/randomization',   factory=models.PatientFactory, traverse='/{patient}/enrollments/{enrollment}')

    config.add_route('studies.visits',                      '/patients/{patient}/visits',                       factory=models.PatientFactory, traverse='/{patient}/visits')
    config.add_route('studies.visits_cycles',               '/patients/{patient}/visits/cycles',                factory=models.PatientFactory, traverse='/{patient}/visits')
    config.add_route('studies.visit',                       '/patients/{patient}/visits/{visit}',               factory=models.PatientFactory, traverse='/{patient}/visits/{visit}')

    config.add_route('studies.visit_forms',                 '/patients/{patient}/visits/{visit}/forms',         factory=models.PatientFactory, traverse='/{patient}/visits/{visit}/forms')
    config.add_route('studies.visit_form',                  '/patients/{patient}/visits/{visit}/forms/{form}',  factory=models.PatientFactory, traverse='/{patient}/visits/{visit}/forms/{form}')


    config.add_route('studies.cycles',                      '/{study}/cycles',          factory=models.StudyFactory, traverse='/{study}/cycles')
    config.add_route('studies.cycle',                       '/{study}/cycles/{cycle}',  factory=models.StudyFactory, traverse='/{study}/cycles/{cycle}')

    config.add_route('studies.index',                       '/',                        factory=models.StudyFactory)
    config.add_route('studies.study',                       '/{study}',                 factory=models.StudyFactory, traverse='/{study}')
    config.add_route('studies.study_schedule',              '/{study}/schedule',        factory=models.StudyFactory, traverse='/{study}')
    config.add_route('studies.study_enrollments',           '/{study}/enrollments',     factory=models.StudyFactory, traverse='/{study}')
    config.add_route('studies.external_services',           '/{study}/external-services', factory=models.StudyFactory, traverse='/{study}')
    config.add_route('studies.study_visits',                '/{study}/visits',          factory=models.StudyFactory, traverse='/{study}')
    config.add_route('studies.study_visits_cycle',          '/{study}/visits/{cycle}',  factory=models.StudyFactory, traverse='/{study}')
    config.add_route('studies.study_schemata',              '/{study}/schemata',        factory=models.StudyFactory, traverse='/{study}')
    config.add_route('studies.study_schema',                '/{study}/schemata/{schema}', factory=models.StudyFactory, traverse='/{study}')

    log.debug('Routes configured')
