from setuptools import find_packages
from setuptools import setup


# Working release version
version = '0.5.1'


setup(
    name='avrc.data.store',
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
    keywords='AVRC BEAST datastore database eav sqlalchemy relational clinical',
    author='BEAST Core Development Team',
    author_email='beast@ucsd.edu',
    url='https://github.com/beastcore/avrc.data.store',
    license='GPL',
    packages=find_packages('src', exclude=['ez_setup']),
    package_dir={'':'src'},
    namespace_packages=['avrc', 'avrc.data'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',

        # ZOPE component functionality
        'zope.component',
        'zope.configuration',
        'zope.deprecation',
        'zope.i18nmessageid',

        # Component specification/documentation
        'zope.interface',
        'zope.schema',

        # Batching support
        'z3c.batching',

        # Interface directives for schemata
        'martian',

        # ORM utilities and upgrade tools
        'SQLAlchemy',
        'sqlalchemy-migrate',

        ],
    extras_require=dict(
        postgresql=['psycopg2'],
        test=['plone.testing'],
        ),
    tests_require=['plone.testing'],
    test_suite='avrc.data.store.tests',
    )
