from setuptools import setup, find_packages
import os

version = u'1.0.0b1'

setup(
    name=u'occams.roster',
    version=version,
    description=u'',
    classifiers=[
        u'Development Status :: 4 - Beta'
        u'Framework :: Plone',
        u'Intended Audience :: Developers'
        u'Operating System :: OS Independent'
        u'Programming Language :: Python',
        u'Topic :: Database',
        u'Topic :: Scientific/Engineering :: Bio-Informatics',
        u'Topic :: Scientific/Engineering :: Information Analysis',
        u'Topic :: Scientific/Engineering :: Medical Science Apps.',
        u'Topic :: Software Development :: Libraries',
        u'Topic :: Utilities',
        ],
    keywords=u'OCCAMS HIVe BEAST database roster clinical sqlalchemy',
    author=u'BIT Core Development Team',
    author_email=u'bitcore@ucsd.edu',
    url=u'https://github.com/beastcore/occams.roster.git',
    license=u'GPL',
    packages=find_packages('src', exclude=['ez_setup']),
    package_dir={'':'src'},
    namespace_packages=['occams'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'SQLAlchemy',
        'sqlalchemy-migrate',
        ],
    extras_require={
        'postgres': ['psycopg2'],
        'test': [ 'nose', 'rudolf', 'WebTest', 'coverage', ]
        },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
    )

