
from pyramid.path import DottedNameResolver
from pyramid.view import view_config


@view_config(
    route_name='occams.main',
    permission='view',
    renderer='../templates/root.pt')
def root(context, request):
    """
    Renders all available applciations
    """

    resolver = DottedNameResolver()

    apps = []

    for dotted in request.registry.settings['occams.apps']:
        module = resolver.resolve(dotted)
        if hasattr(module, '__prefix__'):
            apps.append({
                'name': dotted,
                'title': module.__title__,
                # TODO: maybe use a default view instead?
                'url': module.__prefix__
            })

    apps = sorted(apps, key=lambda v: v['title'])

    return {
        'apps': apps,
        }
