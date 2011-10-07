from setuptools import find_packages
from setuptools import setup


# Working release version
version = '0.4.0'


setup(
    name='hive.form',
    version=version,
    description='A tool for managing DataStore forms in Plone',
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
    url='https://github.com/beastcore/hive.form',
    license='GPL',
    packages=find_packages('src', exclude=['ez_setup']),
    package_dir={'':'src'},
    namespace_packages=['hive'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'plone.app.dexterity',
        'avrc.data.store',
        ],
    extras_require=dict(
        postgresql=['psycopg2'],
        test=['plone.app.testing'],
        ),
    tests_require=['plone.app.testing'],
    test_suite='hive.form.tests',
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
    )
