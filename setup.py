import os
from setuptools import find_packages, setup
from subprocess import Popen, PIPE
import sys

HERE = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(HERE, 'README.rst')).read()
CHANGES = open(os.path.join(HERE, 'CHANGES.rst')).read()

REQUIRES = [
    'alembic',
    'cssmin',
    'jsmin',
    'occams.datastore',
    'pyramid',
    'pyramid_mailer',
    'pyramid_redis_sessions',
    'pyramid_redis',
    'pyramid_tm',
    'pyramid_rewrite',
    'pyramid_webassets',
    'pyramid_who',
    'SQLAlchemy',
    'transaction',
    'wtforms',
    'zope.sqlalchemy',
]

EXTRAS = {
    'postgresql': ['psycopg2'],
    'test': [
        'pyramid_debugtoolbar',
        'nose',
        'coverage',
        'unittest2',
        'WebTest',
        'beautifulsoup4']
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
    name='occams.form',
    version=get_version(),
    description='A web application for managing dynamic forms',
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Pyramid',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
        'Topic :: Database',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Medical Science Apps.',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities',
    ],
    keywords='OCCAMS datastore database eav',
    author='UCSD BIT Core Team',
    author_email='bitcore@ucsd.edu',
    url='https://bitbutcket.org/ucsdbitcore/occams.form',
    license='GPL',
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
    main = occams.form:main
    [console_scripts]
    of_init = occams.form.scripts.initializedb:main
    """,
)
