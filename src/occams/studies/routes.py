# flake8: NOQA
# This module breaks my OCD-ness in favor of readability
from datetime import datetime
from . import log

from . import models


def includeme(config):
    """
    Helper method to configure available routes for the application
    """
    config.add_static_view('static',                'occams.studies:static/')

    config.add_route('socket.io',                   '/socket.io/*remaining')

    config.add_route('login',                       '/login')
    config.add_route('logout',                      '/logout')

    config.add_route('setup',                       '/setup')

    config.add_route('home',                        '/',                            factory=models.StudyFactory)

    config.add_route('sites',                       '/sites')
    config.add_route('site',                        '/sites/{site}')

    config.add_route('reference_types',             '/reference_types')
    config.add_route('reference_type',              '/reference_types/{reference_type}')

    config.add_route('studies',                     '/',                            factory=models.StudyFactory)
    config.add_route('study',                       '/studies/{study}',             factory=models.StudyFactory, traverse='/{study}')
    config.add_route('study_progress',              '/studies/{study}/progress',    factory=models.StudyFactory, traverse='/{study}')

    config.add_route('cycles',                      '/studies/{study}/cycles')
    config.add_route('cycle',                       '/studies/{study}/cycles/{cycle}')

    config.add_route('exports',                     '/exports',                         factory=models.ExportFactory)
    config.add_route('exports_checkout',            '/exports/checkout',                factory=models.ExportFactory)
    config.add_route('exports_status',              '/exports/status',                  factory=models.ExportFactory)
    config.add_route('exports_faq',                 '/exports/faq',                     factory=models.ExportFactory)
    config.add_route('exports_codebook',            '/exports/codebook',                factory=models.ExportFactory)
    config.add_route('export',                      '/exports/{export:\d+}',            factory=models.ExportFactory, traverse='/{export}')
    config.add_route('export_download',             '/exports/{export:\d+}/download',   factory=models.ExportFactory, traverse='/{export}')

    config.add_route('patients',                    '/patients',                        factory=models.PatientFactory, traverse='/{patient}')
    config.add_route('patient',                     '/patients/{patient}',              factory=models.PatientFactory, traverse='/{patient}')
    config.add_route('patient_forms',               '/patients/{patient}/forms',        factory=models.PatientFactory, traverse='/{patient}')
    config.add_route('patient_form',                '/patients/{patient}/forms/{form}', factory=models.PatientFactory, traverse='/{patient}')

    config.add_route('enrollments',                 '/patients/{patient}/enrollments',                              factory=models.PatientFactory)
    config.add_route('enrollment',                  '/patients/{patient}/enrollments/{enrollment}',                 factory=models.PatientFactory, traverse='/{enrollment}')
    config.add_route('enrollment_termination',      '/patients/{patient}/enrollments/{enrollment}/termination',     factory=models.PatientFactory, traverse='/{enrollment}')
    config.add_route('enrollment_randomization',    '/patients/{patient}/enrollments/{enrollment}/randomization',   factory=models.PatientFactory, traverse='/{enrollment}')

    config.add_route('visits',                      '/patients/{patient}/visits',                       factory=models.PatientFactory)
    config.add_route('visit',                       '/patients/{patient}/visits/{visit}',               factory=models.PatientFactory, traverse='/{patient}/visits/{visit}')
    config.add_route('visit_forms',                 '/patients/{patient}/visits/{visit}/forms',         factory=models.PatientFactory, traverse='/{patient}/visits/{visit}')
    config.add_route('visit_form',                  '/patients/{patient}/visits/{visit}/forms/{form}',  factory=models.PatientFactory, traverse='/{patient}/visits/{visit}')

    log.debug('Routes configured')
