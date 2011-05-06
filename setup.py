from setuptools import find_packages
from setuptools import setup


# Working release version
version = '0.3.1'


setup(
    name='avrc.data.store',
    version=version,
    description='Provides storage solution for sparse clinical study data.',
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
    keywords='AVRC BEAST datastore database eav clinical sqlalchemy relational',
    author='BEAST Core Development Team',
    author_email='beast@ucsd.edu',
    url='http://datam0nk3y.org/P01svn/plone4_eggs/avrc.data.store/trunk',
    license='GPL',
    packages=find_packages('src', exclude=['ez_setup']),
    package_dir={'':'src'},
    namespace_packages=['avrc', 'avrc.data'],
    include_package_data=True,
    zip_safe=False,
    # Dependency packages, we leave the exact version requirements to buildout,
    # although with time, we'll start adding version restrictions if issues
    # arise
    install_requires=[
        'setuptools',
        ### Zope 2
        'zope.component', # Adapters/utilities
        'zope.deprecation', # Deprecate unused libraries
        'zope.i18nmessageid', # Internationalization
        'zope.interface', # Specifications
        'zope.schema', # Specification data types
        ### schemata
        # These will be moved into a 'forms' package in the future
        'plone.alterego', # Virtual name spaces
        'plone.autoform', # Form directives
        'plone.supermodel', # Form directives
        'z3c.form',
        ### sql
        'sqlalchemy-migrate',
        'sqlalchemy', # SQLAlchemy, don't support >0.6 yet
        'z3c.saconfig', # for database connectivity until
                                        # we can figure out local utilities
        ],
    extras_require=dict(
        postgresql=['psycopg2'],
        test=['zope.testing'],
        ),
    test_suite='avrc.data.store.tests',
    )
