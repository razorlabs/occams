from pyramid.settings import asbool


def piwik_from_config(settings):
    """
    Parses piwik-specific configurations

    :param settings:    Dictionary of settings to extract from.
                        The following names are processed:

                        * piwik.enabled   - flag to turn on/off
                        * piwik.site      - Site ID of this application
                        * piwik.url       - Piwik URL

    """

    parsed = dict.fromkeys(['piwik.enabled', 'piwik.url', 'piwik.site'])

    enabled = parsed['piwik.enabled'] = asbool(settings['piwik.enabled'])

    if not enabled:
        return parsed

    parsed.update({
        'piwik.url': (settings['piwik.url'] or '').strip(),
        'piwik.site': int(settings['piwik.site'])
    })

    return parsed
