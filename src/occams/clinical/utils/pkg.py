import os
import pkg_resources


def resolve_path(spec, validate=False):
    """
    Resolves an asset descriptor
    """
    if ':' in spec:
        package, path = spec.split(':')
        spec = pkg_resources.resource_filename(package, path)

    spec = os.path.abspath(spec)

    if validate:
        assert os.path.exists(spec), 'Path does not exist: %s' % spec

    return spec
