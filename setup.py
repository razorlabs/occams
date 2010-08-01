from setuptools import setup, find_packages
import os

setup(
    name='avrc.data.store',
    version="0.1",
    description="Provides storage solution for sparse clinical study data",
    long_description=open("README.txt").read() + "\n" +
                     open(os.path.join("docs", "HISTORY.txt")).read(),
    # More at: http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
      "Framework :: Plone",
      "Programming Language :: Python",
      # -*- Additional classifiers -*-
      "Topic :: Database",
      "Topic :: Scientific/Engineering :: Bio-Informatics",
      "Topic :: Scientific/Engineering :: Information Analysis",
      "Topic :: Scientific/Engineering :: Medical Science Apps.",
      "Topic :: Utilities",
      ],
    keywords='',
    author='Viral Evolution Group',
    author_email='monkeybusiness@ucsd.edu',
    url='http://datam0nk3y.org/P01svn/plone4_eggs/avrc.data.store',
    license='GPL',
    packages=find_packages('src', exclude=['ez_setup']),
    package_dir = {'':'src'},
    namespace_packages=['avrc', 'avrc.data'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        # -*- Extra requirements: -*-
        # --- ZOPE Base
        "zope.interface",
        "zope.schema",
        "zope.component",
        "zope.i18nmessageid",
        # --- Database
        # Use the latest version instead of the built-in one
        "pysqlite",
        "SQLAlchemy>=0.5.8,<0.5.99",
        # --- Helper modules
        # --- Forms
        "plone.app.z3cform",
        "plone.app.dexterity",
        "plone.directives.form"
    ],
    entry_points="""
    # -*- Entry points: -*-

    [z3c.autoinclude.plugin]
    target = plone
    """,
    )
