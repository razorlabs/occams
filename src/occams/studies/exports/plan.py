class ExportPlan(object):
    """
    An export plan
    Sublasses should specify how their data should be exported.
    """

    name = None             # System name
    title = None            # Display name

    has_private = False     # Contains private (PHI) data
    has_rand = False        # Contains restricted (Rand) data

    versions = []           # All versions avaialble

    @property
    def file_name(self):
        return self.name + '.csv'

    def codebook(self):
        """
        Generate codebook data

        Returns:
        An iterator or row codebook entries
        """
        raise NotImplemented  # pragma: nocover

    def data(self, use_choice_labels=False, expand_collections=False):
        """
        Generate export data

        Parameters:
        use_choice_labels -- (Optional) Use choice labels instead of codes,
                             default: False
        expand_collections -- (Optional) Examnd multi-selects to one column per
                              possible choice.
                              default: False

        Returns:
        An iterator of row data
        """
        raise NotImplemented  # pragma: nocover

    def to_json(self):
        """
        Serialize to JSON
        """
        keys = ('name', 'title', 'has_private', 'has_rand')
        ret = dict((k, getattr(self, k)) for k in keys)
        ret['versions'] = list(map(str, self.versions))
        return ret
