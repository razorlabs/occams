from pyramid.security import Allow, Authenticated, ALL_PERMISSIONS


class RootFactory(object):

    __acl__ = [
        (Allow, 'administrators', ALL_PERMISSIONS),
        (Allow, 'managers', ('view',)),
        (Allow, 'primary_investigators', ('view',)),
        (Allow, 'data_enterers', ('view',)),
        (Allow, 'assistants', ('view',)),
        (Allow, 'nurses', (
            'view'
            'site_view',
            'patient_add',  'patient_view',  'patient_edit',
            'enrollment_add',  'enrollment_view',  'enrollment_edit',
            'enrollment_delete',
            'visit_add',  'visit_view',  'visit_edit',  'visit_delete')),
        (Allow, Authenticated, 'view'),
        ]

    def __init__(self, request):
        self.request = request


class SiteFactory(object):
    # TODO: future location of per-site access
    pass
