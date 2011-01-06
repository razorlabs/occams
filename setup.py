from setuptools import find_packages
from setuptools import setup


# Working release version
version = '0.1.4'


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
    keywords='AVRC datastore database eav clinical sqlalchemy relational',
    author='UCSD AntiViral Research Center',
    author_email='avrcdata@ucsd.edu',
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
        'zope.component',               # Adapters/utilities
        'zope.configuration',           # For command-line usage (loads hooks)
        'zope.deprecation',             # Deprecate unused libraries
        'zope.i18nmessageid',           # Internationalization
        'zope.interface',               # Specifications
        'zope.schema',                  # Specification data types
        ### schemata
        'plone.alterego',               # Virtual name spaces
        'plone.autoform',               # Form directives
        'plone.directives.form',        # Dexterity-style z3c form support
        'plone.supermodel',             # Form directives
        ### sql
        'SQLAlchemy',                   # SQLAlchemy, don't support >0.6 yet
        'sqlalchemy-migrate',
        'transaction',                  # Zope-style transaction integration
        'z3c.saconfig',                 # Name SQLalchemy utilities
        ],
    extras_require=dict(test=['zope.testing']),
    test_suite='avrc.data.store.tests',
    )
