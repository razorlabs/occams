import os
from subprocess import Popen, PIPE
import sys

from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(HERE, 'README.txt')).read()
CHANGES = open(os.path.join(HERE, 'CHANGES.txt')).read()

requires = [
    'alembic',
    'beaker',
    'celery',
    'colander',
    'cssmin',
    'gevent-socketio',
    'jsmin',
    'pyramid>=1.4.0,<1.4.99',
    'pyramid_celery',
    'pyramid_debugtoolbar',
    'pyramid_layout',
    'pyramid_ldap',
    'pyramid_tm',
    'pyramid_webassets',
    'PyYAML',
    'SQLAlchemy>=0.8.0,<0.8.99',
    'transaction',
    'waitress',
    'webassets',
    'zope.sqlalchemy',

    'occams.datastore',
    'occams.form',
    'occams.roster',
    ]


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
            .strip())
    except:
        version_git = None

    version = version_git or version_txt

    if not version:
        raise ValueError('Could not determine version')

    # update fallback file if necessary
    if version != version_txt:
        with open(version_file, 'w') as fp:
            fp.write(version)

    return version


setup(
    name='occams.clinical',
    version=get_version(),
    description='occams.clinical',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
    "Programming Language :: Python",
    "Framework :: Pyramid",
    "Topic :: Internet :: WWW/HTTP",
    "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author='',
    author_email='',
    url='',
    keywords='web wsgi bfg pylons pyramid',
    packages=find_packages('src', exclude=['ez_setup']),
    package_dir={'':'src'},
    namespace_packages=['occams'],
    include_package_data=True,
    zip_safe=False,
    test_suite='occams.clinical',
    install_requires=requires,
    extras_require=dict(
        postgresql=['psycopg2', 'psycogreen'],
        test=['plone.testing'], # Required for layers, does not install Plone
        ),
    entry_points="""\
    [paste.app_factory]
    main = occams.clinical:main
    [console_scripts]
    initialize_occams_clinical_db = occams.clinical.cli.initializedb:main
    """,
    )

