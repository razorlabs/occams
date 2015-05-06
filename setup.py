import os
from setuptools import setup, find_packages
from setuptools.command.develop import develop as _develop
import sys

HERE = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(HERE, 'README.rst')).read()
CHANGES = open(os.path.join(HERE, 'CHANGES.rst')).read()


REQUIRES = [
    'alembic>=0.7.6,<0.7.99',           # Database table upgrades
    'babel',                            # i18n
    'celery[redis]>=3.1,<3.1.99',       # Asynchronous queue API
    'cssmin',                           # CSS asset compression
    'gevent-socketio>=0.3.6,<0.3.99',   # websockets
    'gunicorn',                         # WSGI server
    'humanize',                         # human readable measurements
    'jsmin',                            # JS asset compression
    'lingua',                           # i18n
    'gevent-socketio',
    'python-dateutil',                  # Date parsing
    'python-slugify',                   # path-friendly filenames
    'pyramid>=1.5',                     # Framework
    'pyramid_chameleon',                # Templating
    'pyramid_exclog',                   # Logging for production
    'pyramid_tm',                       # Centralized transations
    'pyramid_redis_sessions',           # HTTP session with redis backend
    'pyramid_redis',
    'pyramid_rewrite',                  # Allows urls to end in "/"
    'pyramid_webassets',                # Asset management (ala grunt)
    'pyramid_who',                      # User authentication
    'six',                              # Py 2 & 3 compatibilty
    'SQLAlchemy',                       # Database ORM
    'tabulate',                         # ASCII tables for CLI pretty-print
    'wtforms>=2.0.0',
    'wtforms-json',
    'wtforms-components',
    'zope.sqlalchemy',                  # Connects sqlalchemy to pyramid_tm

    'occams_datastore',                 # It's an utility, not an app
]

EXTRAS = {

    'apps': [                           # Default applications
        'occams_accounts',
        'occams_studies',
        'occams_forms'
        'occams_lims'
        'occams_reports',
    ],

    'docs': [                           # Documentation building
        'sphinx',
        'sphinx-autobuild'
    ],

    'ldap': ['who_ldap'],               # LDAP authorization

    'sqlite': [],

    'postgresql': [
        'psycopg2',
        'psycogreen'
    ],

    'test': [
        'pyramid_debugtoolbar',
        'nose',
        'nose-testconfig',
        'coverage',
        'WebTest',
        'beautifulsoup4',
        'mock',
        'ddt'
    ],
}


if sys.version_info < (2, 7):
    REQUIRES.extend(['argparse', 'ordereddict'])
    EXTRAS['test'].extend(['unittest2'])


if sys.version_info < (3, 0):
    REQUIRES.extend(['unicodecsv'])


def get_version():
    """
    Generates python version from projects git tag
    """
    import os
    from subprocess import Popen, PIPE
    import sys
    here = os.path.abspath(os.path.dirname(__file__))
    version_file = os.path.join(here, 'VERSION')

    # read fallback file
    try:
        with open(version_file, 'r+') as fp:
            version_txt = fp.read().strip()
    except:
        version_txt = None

    # read git version (if available)
    try:
        version_git = (
            Popen(['git', 'describe'], stdout=PIPE, stderr=PIPE, cwd=here)
            .communicate()[0]
            .strip()
            .decode(sys.getdefaultencoding()))
    except:
        version_git = None

    version = version_git or version_txt or '0.0.0'

    # update fallback file if necessary
    if version != version_txt:
        with open(version_file, 'w') as fp:
            fp.write(version)

    return version


class _custom_develop(_develop):
    def run(self):
        _develop.run(self)
        self.execute(_post_develop, [], msg="Running post-develop task")


def _post_develop():
    from subprocess import call
    call(['bower', 'install'], cwd=HERE)


setup(
    name='occams',
    version=get_version(),
    description='OCCAMS Application Platform',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author='UCSD BIT Core Team',
    author_email='bitcore@ucsd.edu',
    url='https://bitbutcket.org/ucsdbitcore/occams',
    keywords='web wsgi bfg pylons pyramid',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=REQUIRES,
    extras_require=EXTRAS,
    tests_require=EXTRAS['test'],
    test_suite='nose.collector',
    cmdclass={'develop': _custom_develop},
    entry_points="""\
    [paste.app_factory]
    main = occams:main
    [console_scripts]
    occams_buildassets = occams.scripts.buildassets:main
    """,
)
