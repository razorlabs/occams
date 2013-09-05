import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'alembic',
    'beaker',
    'colander==1.0a5',
    'cssmin',
    'jsmin',
    'pyramid>=1.4.0,<1.4.99',
    'pyramid_debugtoolbar',
    'pyramid_layout',
    'pyramid_ldap',
    'pyramid_tm',
    'pyramid_webassets',
    'SQLAlchemy',
    'SQLAlchemy>=0.8.0,<0.8.99',
    'transaction',
    'waitress',
    'webassets',
    'zope.sqlalchemy',

    'occams.datastore',
    'occams.form',
    'occams.roster',
    ]

setup(
    name='occams.clinical',
    version='1.0.0',
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
        postgresql=['psycopg2'],
        test=['plone.testing'], # Required for layers, does not install Plone
        ),
    entry_points="""\
    [paste.app_factory]
    main = occams.clinical:main
    [console_scripts]
    initialize_occams_clinical_db = occams.clinical.scripts.initializedb:main
    """,
    )
