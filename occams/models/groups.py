class groups:
    """
    Generates the OCCAMS-compatble group names that distinguaish site-level
    permissions.

    There are "dynamic" constants.

    The purpose of this utility is that there are no silent errors if the
    site/group names are mispelled (instead we'll get a synax error).
    """

    @staticmethod
    def principal(site=None, group=None):
        """
        Generates the principal name used internally by this application
        Supported keyword parameters are:
            site --  The site code
            group -- The group name
        """
        return site.name + ':' + group if site else group

    @staticmethod
    def administrator():
        return groups.principal(group='administrator')

    @staticmethod
    def manager(site=None):
        return groups.principal(site=site, group='manager')

    @staticmethod
    def coordinator(site=None):
        return groups.principal(site=site, group='coordinator')

    @staticmethod
    def reviewer(site=None):
        return groups.principal(site=site, group='reviewer')

    @staticmethod
    def enterer(site=None):
        return groups.principal(site=site, group='enterer')

    @staticmethod
    def consumer(site=None):
        return groups.principal(site=site, group='consumer')

    @staticmethod
    def member(site=None):
        return groups.principal(site=site, group='member')
