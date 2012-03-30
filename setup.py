from setuptools import find_packages
from setuptools import setup


# Working release version
version = '1.0.0b'


setup(
    name='occams.datastore',
    version=version,
    description='Provides storage solution for sparse data.',
    classifiers=[
        'Development Status :: 4 - Beta'
        'Framework :: Zope3',
        'Intended Audience :: Developers'
        'Operating System :: OS Independent'
        'Programming Language :: Python',
        'Topic :: Database',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Medical Science Apps.',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities',
        ],
    keywords='AVRC BIT OCCAMS datastore database eav sqlalchemy relational clinical',
    author='BIT Core Development Team',
    author_email='bitcore@ucsd.edu',
    url='https://github.com/bitcore/occams.datastore',
    license='GPL',
    packages=find_packages('src', exclude=['ez_setup']),
    package_dir={'':'src'},
    namespace_packages=['occams'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',

        # Component specification/documentation
        'zope.deprecation',
        'zope.i18nmessageid',
        'zope.interface',
        'zope.schema',

        # Batching support
        'z3c.batching',

        # ORM utilities and upgrade tools
        'SQLAlchemy',
        'alembic',
        ],
    extras_require=dict(
        postgresql=['psycopg2'],
        zope=[
            'zope.component',
            'zope.configuration',
            ],
        test=['plone.testing'],
        ),
    tests_require=['plone.testing'],
    test_suite='occams.datastore.tests',
    )
