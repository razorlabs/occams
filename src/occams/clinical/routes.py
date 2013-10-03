"""
Route Declarations
"""

from datetime import datetime


def config_routes(config):
    """
    Helper method to configure available routes for the application
    """
    ymd = dates('date')

    # short-hand way to declare the routes
    route = config.add_route

    config.add_static_view('occams_clinical_static', 'occams.clinical:static/')

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

    route('quick_add', '/add')

    route('visit_list', '/patients/{pid}/visits')
    route('visit_add', '/patients/{pid}/visits/add')
    route('visit_view', '/patients/{pid}/visits/{vist_date}', custom_predicates=[ymd])
    route('visit_edit', '/patients/{pid}/visits/{visit_date}/edit', custom_predicates=[ymd])
    route('visit_delete', '/patients/{pid}/visits/{visit_date}/delete', custom_predicates=[ymd])

    route('data_list', '/data')
    route('data_export', '/data/export')
    route('data_custom', '/data/custom')

    route('socket_io', '/socket.io/*')

    return config


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

