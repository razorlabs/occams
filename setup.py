import os
from setuptools import find_packages, setup
from setuptools.command.develop import develop as _develop


HERE = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(HERE, 'README.rst')).read()
CHANGES = open(os.path.join(HERE, 'CHANGES.rst')).read()

REQUIRES = [
    'alembic',                          # Database table upgrades
    'cssmin',                           # CSS asset compression
    'jsmin>=2.0.11',                    # JS asset compression
    'python-dateutil',                  # Date parsing
    'pyramid>=1.5',                     # Framework
    'pyramid_chameleon',                # Templating
    'pyramid_redis_sessions==1.0a2',    # HTTP session with redis backend
    'pyramid_tm',                       # Centralized request transactions
    'pyramid_rewrite',                  # Allows urls to end in "/"
    'pyramid_webassets',                # Asset managements (ala grunt)
    'pyramid_who',                      # User authentication
    'six',                              # Py 2 & 3 compatibility
    'SQLAlchemy>=0.9.0',                # Database ORM
    'wtforms>=2.0.0',
    'wtforms-json',
    'zope.sqlalchemy',                  # Connects sqlalchemy to pyramid_tm

    'occams.datastore',                 # EAV
]

EXTRAS = {
    'ldap': ['who_ldap'],
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
    call(['npm', 'install'], cwd=HERE)
    call(['./node_modules/.bin/bower', 'install'], cwd=HERE)


setup(
    name='occams.forms',
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
    url='https://bitbutcket.org/ucsdbitcore/occams.forms',
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
    cmdclass={'develop': _custom_develop},
    entry_points="""\
    [paste.app_factory]
    main = occams.forms:main
    [console_scripts]
    of_initdb = occams.forms.scripts.initdb:main
    """,
)
