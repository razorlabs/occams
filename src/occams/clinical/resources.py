from pyramid.security import Allow, Authenticated, ALL_PERMISSIONS


class RootFactory(object):

    __acl__ = [
        (Allow, 'administrator', ALL_PERMISSIONS),
        (Allow, 'investigator', (
            'view',
            'fia_view')),
        (Allow, 'coordinator', (
            'view',
            'fia_view')),
        (Allow, 'statistician', (
            'view',
            'fia_view')),
        (Allow, 'researcher', (
            'view',
            'fia_view')),
        (Allow, 'nurse', (
            'view'
            'site_view',
            'patient_add',  'patient_view',  'patient_edit',
            'enrollment_add',  'enrollment_view',  'enrollment_edit',
            'enrollment_delete',
            'visit_add',  'visit_view',  'visit_edit',  'visit_delete',
            'fia_view')),
        (Allow, 'assistant', ('view',)),
        (Allow, 'student', ('view',)),
        (Allow, Authenticated, 'view'),
        ]

    def __init__(self, request):
        self.request = request


class SiteFactory(object):
    # TODO: future location of per-site access
    pass
