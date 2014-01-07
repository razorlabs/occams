import os
from subprocess import Popen, PIPE
from setuptools import setup, find_packages
import sys

HERE = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(HERE, 'README.md')).read()
CHANGES = open(os.path.join(HERE, 'CHANGES.md')).read()


REQUIRES = [
    'alembic',
    'beaker',
    'celery',
    'colander',
    'cssmin',
    'deform',
    'gevent-socketio',
    'jsmin',
    'pyramid',
    'pyramid_beaker',
    'pyramid_deform',
    'pyramid_layout',
    'pyramid_mailer',
    'pyramid_tm',
    'pyramid_rewrite',
    'pyramid_webassets',
    'pyramid_who',
    'redis',
    'SQLAlchemy',
    'transaction',
    'webassets',
    'zope.sqlalchemy',
    'zope.dottedname',

    'occams.datastore',
    'occams.form',
    'occams.roster',
]

EXTRAS = {
    'postgresql': ['psycopg2', 'psycogreen'],
    'test': [
        'pyramid_debugtoolbar',
        'nose', 'rednose',
        'coverage',
        'WebTest',
        'beautifulsoup4'],
}


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
    author='UCSD BIT Core Team',
    author_email='bitcore@ucsd.edu',
    url='https://bitbutcket.org/ucsdbitcore/occams.clinical',
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
    main = occams.clinical:main
    [console_scripts]
    cl_init = occams.clinical.scripts.initializedb:main
    """,
)
