import os
from subprocess import Popen, PIPE
from setuptools import setup, find_packages
import sys

HERE = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(HERE, 'README.rst')).read()
CHANGES = open(os.path.join(HERE, 'CHANGES.rst')).read()


REQUIRES = [
    'alembic',                          # Database table upgrades
    'babel',                            # i18n
    'celery[redis]>=3.1,<3.1.99',       # Asynchronous queue API
    'cssmin',                           # CSS asset compression
    'gevent-socketio>=0.3.6,<0.3.99',   # websockets
    'good>=0.0.7',                      # Input validation
    'humanize',                         # human readable measurements
    'jsmin',                            # JS asset compression
    'lingua',                           # i18n
    'Paste',                            # Needed for urlmap
    'pyramid>=1.5',                     # Framework
    'pyramid_chameleon',                # Templating
    'pyramid_tm',                       # Centralized transations
    'pyramid_redis_sessions==1.0a2',    # HTTP session with redis backend
    'pyramid_rewrite',                  # Allows urls to end in "/"
    'pyramid_webassets',                # Asset management (ala grunt)
    'pyramid_who',                      # User authentication
    'six',                              # Py 2 & 3 compatibilty
    'SQLAlchemy>=0.9.0',                # Database ORM
    'tabulate',                         # ASCII tables for CLI pretty-print
    'zope.sqlalchemy',                  # Connects sqlalchemy to pyramid_tm

    'occams.datastore',                 # EAV
    'occams.forms',                     # EAV form renderer
]

EXTRAS = {
    'ldap': ['python3-ldap', 'who_ldap'],
    'sqlite': [],
    'postgresql': ['psycopg2', 'psycogreen'],
    'gunicorn': ['gunicorn'],
    'test': [
        'pyramid_debugtoolbar',
        'nose',
        'nose-testconfig',
        'coverage',
        'WebTest',
        'beautifulsoup4',
        'mock',
        'ddt'],
}


if sys.version_info < (2, 7):
    REQUIRES.extend(['argparse', 'ordereddict'])
    EXTRAS['test'].extend(['unittest2'])


if sys.version_info < (3, 0):
    REQUIRES.extend(['unicodecsv'])


def get_version():
    version_file = os.path.join(HERE, 'VERSION')

    # read fallback file
    try:
        with open(version_file, 'r+') as fp:
            version_txt = fp.read().strip()
    except:
        version_txt = None

    # read git version (if available)
    try:
        version_git = (
            Popen(['git', 'describe'], stdout=PIPE, stderr=PIPE, cwd=HERE)
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


setup(
    name='occams.studies',
    version=get_version(),
    description='occams.studies',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author='UCSD BIT Core Team',
    author_email='bitcore@ucsd.edu',
    url='https://bitbutcket.org/ucsdbitcore/occams.studies',
    keywords='web wsgi bfg pylons pyramid',
    packages=find_packages('src', exclude=['ez_setup']),
    package_dir={'': 'src'},
    namespace_packages=['occams'],
    include_package_data=True,
    zip_safe=False,
    install_requires=REQUIRES,
    extras_require=EXTRAS,
    tests_require=EXTRAS['test'],
    test_suite='nose.collector',
    entry_points="""\
    [paste.app_factory]
    main = occams.studies:main
    [console_scripts]
    os_initdb = occams.studies.scripts.initdb:main
    os_export = occams.studies.scripts.export:main
    """,
)
