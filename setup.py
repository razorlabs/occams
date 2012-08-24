from setuptools import find_packages
from setuptools import setup


# Working release version
version = '1.0.0b1'


setup(
    name='occams.form',
    version=version,
    description='A tool for managing dynamic forms in Plone.',
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
    keywords='OCCAMS datastore database eav sqlalchemy relational clinical',
    author='BEAST Core Development Team',
    author_email='beast@ucsd.edu',
    url='https://github.com/beastcore/occams.form',
    license='GPL',
    packages=find_packages('src', exclude=['ez_setup']),
    package_dir={'':'src'},
    namespace_packages=['occams'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'Pillow',
        'occams.datastore',
        'collective.z3cform.datagridfield',
        'plone.app.dexterity',
        'plone.app.z3cform',
        'plone.directives.form',
        'plone.z3cform',
        'SQLAlchemy',
        'zope.globalrequest',
        'z3c.saconfig',
        'z3c.form',
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
