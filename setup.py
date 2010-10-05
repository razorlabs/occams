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
    # TODO: (mmartinez) I'd like to eventually enable the dependencies in this
    #       setup.py so that the package can be used (optionally) without
    #       Plone.
    install_requires=[
        "setuptools",
        # configuration
        "z3c.autoinclude",              # <includeDependencies>
#        # schemata
#        "plone.alterego",              # virtual name spaces
#        "plone.autoform",              # form directives
#        "plone.directives.form",       # dexterity-style z3c form support
#        "plone.supermodel",            # form directives
        # sql
        "SQLAlchemy>=0.5.8,<0.5.99",    # SQLAlchemy, don't support >0.6 yet
        "z3c.saconfig",                 # zope session/engine utilities
#        # Zope 2
#        "transaction",
#        "zope.app.container",
#        "zope.component",
#        "zope.event",
#        "zope.i18nmessageid",
#        "zope.interface",
#        "zope.lifecycleevent",
#        "zope.schema",
    ],
#    extras_require = {
#        # packages for verifying integrity of module
#        'test': [
#            "Zope",
#            "Products.PloneTestCase",
#            "zope.app.component",
#            "zope.app.folder",
#            "zope.testing",
#            "ZopeTestCase",
#            ],
#    },
#    test_suite="avrc.data.store.tests.",
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
    )
