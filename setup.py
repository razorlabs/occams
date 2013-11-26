from setuptools import find_packages
from setuptools import setup


# Working release version
version = '1.0.0b11'


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
        'argparse',

        # Useful tool for result sets
        'ordereddict',

        # Import/Export support via XML
        'lxml',

        # ORM utilities and upgrade tools
        'SQLAlchemy >=0.7.0,<0.7.99',
        'sqlalchemy-migrate >=0.7.0,<0.7.99',

        # Component specification/documentation
        # Note that these packages do not install the entire Zope ecosystem,
        # they install necessary building blocks that are useful merely for
        # specification and documentation.
        'zope.component',
        'zope.deprecation',
        'zope.i18nmessageid',
        'zope.interface',
        'zope.schema',

        # Low-level batching support for Zope products
        'z3c.batching',
        ],
    extras_require=dict(
        postgresql=['psycopg2'],
        test=['plone.testing'], # Required for layers, does not install Plone
        ),
    tests_require=['plone.testing'],
    )
