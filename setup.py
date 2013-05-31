import os
import re
from setuptools import find_packages, setup


here = os.path.abspath(os.path.dirname(__file__))
read = lambda *args: open(os.path.join(*args)).read()

README = read(here, 'README.rst')
CHANGES = read(here, 'CHANGES.rst')
VERSION = re.compile(r'.*__version__\s*=\s*\'(.+?)\'', re.S).match(
        read(here, 'src', 'occams', 'form', '__init__.py')).group(1)

REQUIRES = [
    'argparse',
    'colander',
    'deform',
    'pyramid',
    'SQLAlchemy',
    'transaction',
    'pyramid_beaker',
    'pyramid_deform',
    'pyramid_mailer',
    'pyramid_layout',
    'pyramid_tm',
    'pyramid_debugtoolbar',
    'pyramid_rewrite',
    'pyramid_webassets',
    'cssmin',
    'jsmin',
    'xlutils',
    'zope.sqlalchemy',
    'waitress',
    'webhelpers',
    'occams.datastore',

    # Need these packages for the app to start,
    # we'll be removing them as we transition to Pyramid
    'collective.z3cform.datagridfield',
    'plone.app.dexterity[grok]',
    'plone.app.z3cform',
    'plone.directives.form',
    'plone.z3cform',
    'zope.globalrequest',
    'z3c.saconfig',
    'z3c.form',
    'collective.saconnect',
    'plone.app.testing',
    ]

EXTRAS = {
    'postgresql': ['psycopg2'],
    'test': [ 'nose', 'rudolf', 'WebTest', 'coverage', ]
    }

setup(
    name='occams.form',
    version=VERSION,
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
    keywords='OCCAMS datastore database eav sqlalchemy relational clinical pyramid',
    author='UCSD BIT Core Team',
    author_email='bitcore@ucsd.edu',
    url='https://bitbutcket.org/ucsdbitcore/occams.clinical',
    license='GPL',
    packages=find_packages('src', exclude=['ez_setup']),
    package_dir={'':'src'},
    namespace_packages=['occams'],
    include_package_data=True,
    zip_safe=False,
    install_requires=REQUIRES,
    extras_require=EXTRAS,
    tests_require=EXTRAS['test'],
    entry_points="""\
    [paste.app_factory]
    main = occams.form:main
    [console_scripts]
    initialize_form_db = occams.form.scripts.initializedb:main
    """,
    )

