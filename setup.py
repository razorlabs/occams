from setuptools import setup, find_packages
import os

version = '0.4.2'

setup(
    name='hive.roster',
    version=version,
    description='',
    classifiers=[
        'Development Status :: 4 - Beta'
        'Framework :: Plone',
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
    keywords='HIVe BEAST database roster clinical sqlalchemy',
    author='BEAST Core Development Team',
    author_email='beast@ucsd.edu',
    url='https://github.com/beastcore/hive.roster',
    license='GPL',
    packages=find_packages('src', exclude=['ez_setup']),
    package_dir={'':'src'},
    namespace_packages=['hive'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'SQLAlchemy',
        'sqlalchemy-migrate',
        'z3c.saconfig',
        ],
    extras_require=dict(
        postgresql=['psycopg2'],
        test=['plone.app.testing'],
        ),

    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
    )
