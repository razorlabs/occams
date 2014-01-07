
from pyramid.security import Allow, Authenticated, ALL_PERMISSIONS


class RootFactory(object):
    """
    Default root that enforces application permissions.

    Client applications with their own principles should define
    their own ``who.callback`` that maps client groups to application
    groups.
    """

    __acl__ = [
        (Allow, 'administrators', ALL_PERMISSIONS),
        (Allow, 'managers', (
            'form_add', 'form_edit', 'form_delete',
            'form_amend', 'form_retract', 'form_publish',
            'form_export',
            'workflow_add', 'work_edit', 'workflow_delete',
            )),
        (Allow, 'editors', (
            'form_add', 'form_edit', 'form_delete',
            'form_export',
            )),
        (Allow, Authenticated, 'view'),
        ]

    def __init__(self, request):
        self.request = request
