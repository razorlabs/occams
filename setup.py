import os
import re
from setuptools import find_packages, setup
import sys


here = os.path.abspath(os.path.dirname(__file__))
read = lambda *args: open(os.path.join(*args)).read()

README = read(here, 'README.rst')
CHANGES = read(here, 'CHANGES.rst')

version = '1.0.0'

REQUIRES = [
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
    # Not Python 3 compatible
    #'xlutils',
    'zope.sqlalchemy',
    'waitress',
    'webhelpers',
    'occams.datastore',
    ]

EXTRAS = {
    'postgresql': ['psycopg2'],
    'test': [ 'nose', 'rudolf', 'WebTest', 'coverage', ]
    }

if sys.version_info < (2, 7):
    REQUIRES += ['argparse',]


setup(
    name='occams.form',
    version=version,
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

