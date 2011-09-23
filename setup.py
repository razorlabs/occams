from setuptools import find_packages
from setuptools import setup


# Working release version
version = '0.4.0'


setup(
    name='hive.form',
    version=version,
    description='Provides UI tools for management of EAV-type forms',
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
    url='http://datam0nk3y.org/P01svn/plone4_eggs/hive.form/trunk',
    license='GPL',
    packages=find_packages('src', exclude=['ez_setup']),
    package_dir={'':'src'},
    namespace_packages=['hive'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',

        # Component specification/documentation
        'zope.i18nmessageid'
        'zope.interface',
        'zope.schema',

        # Plone-specific entry points
        'five.grok',
        'plone.dexterity',

        # ORM utilities and upgrade tools
        'SQLAlchemy',
        'sqlalchemy-migrate',

        # Custom add-on dependencies
        # EAV tools
        'avrc.data.store',
        ],
    extras_require=dict(
        test=['zope.testing'],
        ),
    tests_require=['zope.testing'],
    test_suite='hive.form',
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
    )
