from datetime import datetime

from . import log


def includeme(config):
    """
    Helper method to configure available routes for the application
    """
    ymd = dates('date')

    config.add_static_view('static', 'occams.studies:static/')

    r = config.add_route

    r('socket.io',           '/socket.io/*remaining')

    r('login',               '/login')
    r('logout',              '/logout')

    r('sites',               '/sites')
    r('site',                '/sites/{site}')

    r('reference_types',     '/reference_types')
    r('reference_type',      '/reference_types/{reference_type}')

    r('studies',             '/')
    r('study',               '/studies/{study}')
    r('study_schedule',      '/studies/{study}/schedule')
    r('study_ecrfs',         '/studies/{study}/ecrfs')
    r('study_progress',      '/studies/{study}/progress')

    r('cycles',              '/studies/{study}/cycles')
    r('cycle',               '/studies/{study}/cycles/{cycle}')

    r('exports',             '/exports')
    r('exports_checkout',    '/exports/checkout')
    r('exports_status',      '/exports/status')
    r('exports_faq',         '/exports/faq')
    r('exports_codebook',    '/exports/codebook')
    r('export',              '/exports/{export:\d+}')
    r('export_download',     '/exports/{export:\d+}/download')

    r('patients',
        '/patients',
        factory='.permissions.PatientFactory',
        traverse='/{patient}')
    r('patient',
        '/patients/{patient}',
        factory='.permissions.PatientFactory',
        traverse='/{patient}')
    r('patient_forms',
        '/patients/{patient}/forms',
        factory='.permissions.PatientFactory',
        traverse='/{patient}')
    r('patient_form',
        '/patients/{patient}/forms/{form}',
        factory='.permissions.PatientFactory',
        traverse='/{patient}')

    r('enrollments',
        '/patients/{patient}/enrollments',
        factory='.permissions.PatientFactory',
        traverse='/{patient}')
    r('enrollment',
        '/patients/{patient}/enrollments/{enrollment}',
        factory='.permissions.PatientFactory',
        traverse='/{patient}')

    r('enrollment_termination',
        '/patients/{patient}/enrollments/{enrollment}/termination',
        factory='.permissions.PatientFactory',
        traverse='/{patient}')

    r('enrollment_randomization',
        '/patients/{patient}/enrollments/{enrollment}/randomization',
        factory='.permissions.PatientFactory',
        traverse='/{patient}')

    r('visits',
        '/patients/{patient}/visits',
        factory='.permissions.PatientFactory',
        traverse='/{patient}')
    r('visit',
        '/patients/{patient}/visits/{visit}',
        factory='.permissions.PatientFactory',
        traverse='/{patient}',
        custom_predicates=[ymd])
    r('visit_forms',
        '/patients/{patient}/visits/{visit}/forms',
        factory='.permissions.PatientFactory',
        traverse='/{patient}',
        custom_predicates=[ymd])
    r('visit_form',
        '/patients/{patient}/visits/{visit}/forms/{form}',
        factory='.permissions.PatientFactory',
        traverse='/{patient}',
        custom_predicates=[ymd])

    r('home', '/')

    log.debug('Routes configured')


def dates(*keys):
    """
    Creates function to parse date segments in URL on dispatch.
    """
    def strpdate(str):
        return datetime.strptime(str, '%Y-%m-%d').date()

    def predicate(info, request):
        for key in keys:
            try:
                info['match'][key] = strpdate(info['match'][key])
            except ValueError:
                return False
        return True

    return predicate
