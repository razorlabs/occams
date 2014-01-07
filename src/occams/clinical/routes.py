"""
Route Declarations
"""

from datetime import datetime


def includeme(config):
    """
    Helper method to configure available routes for the application
    """
    ymd = dates('date')

    # short-hand way to declare the routes
    route = config.add_route
    config.include('pyramid_rewrite')
    config.add_rewrite_rule(r'/(?P<path>.*)/', r'/%(path)s')

    config.add_static_view('occams_clinical_static', 'occams.clinical:static/')


    # builtins views (move to core)
    config.add_route('account_login', '/login')
    config.add_route('account_logout', '/logout')
    config.add_route('account', '/account')
    config.add_route('apps', '/apps')

    # instnance-wide views
    config.add_route('socketio', '/socket.io/*remaining')

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

    route('data_list', '/data')
    route('data_download', '/data/download')

    route('clinical', '/')

    config.scan('occams.clinical.layouts')
    config.scan('occams.clinical.panels')
    config.scan('occams.clinical.views')


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
