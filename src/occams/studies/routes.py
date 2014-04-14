"""
Route Declarations
"""

from datetime import datetime

from . import log


def includeme(config):
    """
    Helper method to configure available routes for the application
    """
    ymd = dates('date')

    # short-hand way to declare the routes
    route = config.add_route

    config.add_static_view('static', 'occams.studies:static/')

    route('socket.io', '/socket.io/*remaining')

    route('account_login', '/login')
    route('account_logout', '/logout')

    route('site_list', '/sites')

    route('study_list', '/studies')
    route('study_add', '/studies/add')
    route('study_view', '/studies/{study_name}')
    route('study_edit', '/studies/{study_name}/edit')
    route('study_delete', '/studies/{study_name}/delete')
    route('study_schedule', '/studies/{study_name}/schedule')
    route('study_ecrfs', '/studies/{study_name}/ecrfs')
    route('study_progress', '/studies/{study_name}/progress')

    route('schedule_view', '/studies/{study_name}/{cycle_name}')

    route('patient_search', '/patients')
    route('patient_view', '/patients/{pid}')

    route('event_add', '/events/add')

    route('event_list', '/patients/{pid}/events')
    route(
        'event_view',
        '/patients/{pid}/events/{vist_date}',
        custom_predicates=[ymd])
    route(
        'event_edit',
        '/patients/{pid}/events/{event_date}/edit',
        custom_predicates=[ymd])
    route(
        'event_delete',
        '/patients/{pid}/events/{event_date}/delete',
        custom_predicates=[ymd])

    route('export_home',        '/exports')
    route('export_faq',         '/exports/faq')
    route('export_add',         '/exports/add')
    route('export_status',      '/exports/status')
    route('export_download',    '/exports/{id:\d+}/download')
    route('export_delete',      '/exports/{id:\d+}/delete')

    route('studies', '/')

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
