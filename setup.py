from setuptools import setup, find_packages
import os

version = '0.1'

description = "Responsible for handling the storage capabilities of AVRC data."

setup(name='avrc.data.store',
      version=version,
      description=description,
#      long_description=open("README.txt").read() + "\n" +
#                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
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
          "Elixir",
          "SQLAlchemy>=0.5.8,<0.5.99",
          "z3c.saconfig",
          "plone.app.z3cform",
          "plone.app.dexterity",
          "xlutils",
          "collective.saconnect"
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
