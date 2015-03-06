OCCAMS Forms
============

A web application for managing dynamic forms.


Rationale
---------

As part of the OCCAMS suite of components, a method for accessing and managing
forms through the web is needed for patient data.


Goals
-----

Some goals of this product:

  * Handle form entry
  * Facilitate form managmement
  * Form importing/exporting


System Requirements
-------------------

  * Python 2.7+
  * npm
    - lessc (must be installed globally, i.e. with "-g" option)
  * redis
  * PostgreSQL 9.3+


Authentication
++++++++++++++

Because many organizations have their politics of authentication, this app
tries to not force any authentication paradigm on the client and instead
uses `repoze.who` to allow clients to supply their own authentication via
customized-organization-specific plugins.


Installation
------------

The current version of this application heavily relies on occams.studies for
installation and setup. In the future we hope to make this a ful-fledged
standalone application. For further instructions please refer to ``occams.studies``
documentation.
