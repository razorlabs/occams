"""
Route Declarations
"""

import datetime


def config_routes(config):
    """
    Helper method to configure available routes for the application
    """

    config.add_static_view('static', 'static', cache_max_age=3600)

    config.add_route('home', '')

    config.add_route('account_login', '/login')
    config.add_route('account_logout', '/logout')

    config.add_route('site_list', '/sites')
    config.add_route('site_add', '/sites/add')
    config.add_route('site_view', '/sites/{site_name}')
    config.add_route('site_edit', '/sites/{site_name}/edit')

    config.add_route('study_list', '/studies')
    config.add_route('study_add', '/studies/add')
    config.add_route('study_view', '/studies/{study_name}')
    config.add_route('study_schedule', '/studies/{study_name}/schedule')
    config.add_route('study_schedule_add', '/studies/{study_name}/schedule/add')
    config.add_route('study_schedule_edit', '/studies/{study_name}/schedule/edit')
    config.add_route('study_schedule_delete', '/studies/{study_name}/schedule/delete')
    config.add_route('study_ecrfs', '/studies/{study_name}/ecrfs')
    config.add_route('study_ecrfs_edit', '/studies/{study_name}/ecrfs/edit')
    config.add_route('study_properties', '/studies/{study_name}/properties')
    config.add_route('study_randomization', '/studies/{study_name}/randomization')
    config.add_route('study_edit', '/studies/{study_name}/edit')
    config.add_route('study_delete', '/studies/{study_name}/delete')

    config.add_route('patient_search', '')
    config.add_route('patient_add', '/patients/add')
    config.add_route('patient_view', '/patients/{pid}')
    config.add_route('patient_phi', '/patients/{pid}/phi_ecrfs')
    config.add_route('patient_contact', '/patients/{pid}/contact')
    config.add_route('patient_properties', '/patients/{pid}/properties')
    config.add_route('patient_edit', '/patients/{pid}/edit')
    config.add_route('patient_delete', '/patients/{pid}/delete')

    consent_date = parse_dates('consent_date')
    config.add_route('enrollment_list', '/patients/{pid}/enrollments')
    config.add_route('enrollment_add', '/patients/{pid}/enrollments/add')
    config.add_route('enrollment_view',
        '/patients/{pid}/enrollments/{study_name}-{consent_date:\d+-\d+-\d+}',
        custom_predicates=(consent_date,))
    config.add_route('enrollment_properties',
        '/patients/{pid}/enrollments/{study_name}-{consent_date:\d+-\d+-\d+}/properties',
        custom_predicates=(consent_date,))
    config.add_route('enrollment_edit',
        '/patients/{pid}/enrollments/{study_name}-{consent_date:\d+-\d+-\d+}/edit',
        custom_predicates=(consent_date,))
    config.add_route('enrollment_delete',
        '/patients/{pid}/enrollments/{study_name}-{consent_date:\d+-\d+-\d+}/delete',
        custom_predicates=(consent_date,))

    visit_date = parse_dates('visit_date')
    config.add_route('visit_list',
        '/patients/{pid}/visits')
    config.add_route('visit_add',
        '/patients/{pid}/visits/add')
    config.add_route('visit_view',
        '/patients/{pid}/visits/{visit_date}',
        custom_predicates=(visit_date,))
    config.add_route('visit_edit',
        '/patients/{pid}/visits/{visit_date}/edit',
        custom_predicates=(visit_date,))
    config.add_route('visit_delete',
        '/patients/{pid}/visits/{visit_date}/delete',
        custom_predicates=(visit_date,))

    config.add_route('patient_ecrf_list', '/patients/{pid}/ecrfs')
    config.add_route('patient_ecrf_add', '/patients/{pid}/ecrfs/add')
    config.add_route('patient_ecrf_tabular', '/patients/{pid}/ecrfs/{schema_name}')
    config.add_route('patient_ecrf_view', '/patients/{pid}/ecrfs/{schema_name}/{ecrf_id}')
    config.add_route('visit_ecrf_list',
        '/patients/{pid}/visits/{visit_date}/ecrfs',
        custom_predicates=(visit_date,))
    config.add_route('visit_ecrf_add',
        '/patients/{pid}/visits/{visit_date}/ecrfs/add',
        custom_predicates=(visit_date,))
    config.add_route('visit_ecrf_tabular',
        '/patients/{pid}/visits/{visit_date}/ecrfs/{schema_name}',
        custom_predicates=(visit_date,))
    config.add_route('visit_ecrf_view',
        '/patients/{pid}/visits/{visit_date}/ecrfs/{schema_name}/{ecrf_id}',
        custom_predicates=(visit_date,))
    config.add_route('visit_logs',
        '/patients/{pid}/visits/{visit_date}/logs',
        custom_predicates=(visit_date,))

    config.add_route('export_list', '/exports')

    config.scan()

    return config


def parse_dates(*segment_names):
    """
    Creates function to parse date segments in URL on dispatch.
    """
    def predicate(info, request):
        match = info['match']
        for segment_name in segment_names:
            try:
                raw = match[segment_name]
                parsed = datetime.datetime.strptime(raw, '%Y-%m-%d').date()
                match[segment_name] = parsed
            except ValueError:
                return False
        return True
    return predicate

