from setuptools import find_packages
from setuptools import setup


# Working release version
version = '0.4.0'


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
    author='The BEAST Core Development Team',
    author_email='beast@ucsd.edu',
    url='http://datam0nk3y.org/P01svn/plone4_eggs/avrc.data.store/trunk',
    license='GPL',
    packages=find_packages('src', exclude=['ez_setup']),
    package_dir={'':'src'},
    namespace_packages=['avrc', 'avrc.data'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        ### Zope 2
        'zope.component', # adapter/utility registration
        'zope.configuration', # ZCML support 
        'zope.deprecation', # Deprecation warnings
        'zope.i18nmessageid', # Internationalization
        'zope.interface', # Component specifications
        'zope.schema', # Component property specifications
        ### Interface directives
        'martian',
        ### SQL
        'SQLAlchemy>=0.6.7,<0.6.99', # Backbone of this utility
        'sqlalchemy-migrate>=0.6.1,<0.6.99', # Database schema upgrades
        ],
    extras_require=dict(
        postgresql=['psycopg2'],
        test=['zope.testing'],
        ),
    tests_require=['zope.testing'],
    test_suite='avrc.data.store.tests',
    )
