"""
Route Declarations
"""

from datetime import datetime


def config_routes(config):
    """
    Helper method to configure available routes for the application
    """
    ymd = dates('date')

    config.add_static_view('occams_clinical_static', 'occams.clinical:static/')

    config.add_route('study_list',      '/studies')
    config.add_route('study_add',       '/studies/add')
    config.add_route('study_view',      '/studies/{study_name}')
    config.add_route('study_edit',      '/studies/{study_name}/edit')
    config.add_route('study_delete',    '/studies/{study_name}/delete')
    config.add_route('study_schedule',  '/studies/{study_name}/schedule')
    config.add_route('study_ecrfs',     '/studies/{study_name}/ecrfs')
    config.add_route('study_progress',  '/studies/{study_name}/progress')

    config.add_route('schedule_view',   '/studies/{study_name}/{cycle_name}')

    config.add_route('patient_search',  '/patients')
    config.add_route('patient_view',    '/patients/{pid}')

    config.add_route('quick_add',       '/add')

    config.add_route('visit_list',      '/patients/{pid}/visits')
    config.add_route('visit_add',       '/patients/{pid}/visits/add')
    config.add_route('visit_view',      '/patients/{pid}/visits/{vist_date}',
        custom_predicates=[ymd])
    config.add_route('visit_edit',      '/patients/{pid}/visits/{visit_date}/edit',
        custom_predicates=[ymd])
    config.add_route('visit_delete',    '/patients/{pid}/visits/{visit_date}/delete',
        custom_predicates=[ymd])

    config.add_route('export_list',     '/exports')

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

