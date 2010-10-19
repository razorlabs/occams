from setuptools import setup
from setuptools import find_packages
import os

setup(
    name="avrc.data.store",
    version="0.1",
    description="Provides storage solution for sparse clinical study data",
    long_description=open("README.txt").read() + "\n" +
                     open(os.path.join("docs", "HISTORY.txt")).read(),
    classifiers=[
      "Framework :: Plone",
      "Programming Language :: Python",
      "Topic :: Database",
      "Topic :: Scientific/Engineering :: Bio-Informatics",
      "Topic :: Scientific/Engineering :: Information Analysis",
      "Topic :: Scientific/Engineering :: Medical Science Apps.",
      "Topic :: Utilities",
      ],
    keywords="",
    author="Viral Evolution Group",
    author_email="monkeybusiness@ucsd.edu",
    url="http://datam0nk3y.org/P01svn/plone4_eggs/avrc.data.store",
    license="GPL",
    packages=find_packages("src", exclude=["ez_setup"]),
    package_dir = {"":"src"},
    namespace_packages=["avrc", "avrc.data"],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "setuptools",
        ### Zope 2
        "transaction",                  # Zope-style transaction integration
        "zope.container",               # Local utility support
        "zope.component",               # Adapters/utilities
        "zope.event",                   # Events
        "zope.i18nmessageid",           # Internationalization
        "zope.interface",               # Specifications
        "zope.lifecycleevent",          # Events
        "zope.location",                # Local utility support
        "zope.schema",                  # Specification data types
        "zope.configuration",           # For command-line usage (loads hooks)
        ### schemata
        "plone.alterego",               # Virtual name spaces
        "plone.autoform",               # Form directives
        "plone.directives.form",        # Dexterity-style z3c form support
        "plone.supermodel",             # Form directives
        ### sql
        "SQLAlchemy",                   # SQLAlchemy, don't support >0.6 yet
        "z3c.saconfig",                 # Name SQLalchemy utilities
    ],
    extras_require = {
        # packages for verifying integrity of module
        'test': [
            "zope.testing",
            ],
    },
    test_suite="avrc.data.store.tests",
    # We don't really need entry points as this is simply a utility
    entry_points="""
    """,
    )
