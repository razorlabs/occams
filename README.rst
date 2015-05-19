OCCAMS Accounts
===============

OCCAMS account management.

The current version of this application only functions as a
Single-Sign-On tool. Future versions will handle user management.
As such, please refer to ``occams.studies`` for installation and
configuration.

The primary backbone of this application is `repoze.who`_ because
it offers pluggable authentacation.  To  get a better grasp on how
it works, it is suggested you read through that documentation.

The goal of this project is to be the primary user management tool
for occams, with the option to also pull additional authentication
information from external resources (namely LDAP or ActiveDirectory).
We currently only use LDAP as a stopgap to release.

.. _repoze.who: https://repozewho.readthedocs.org/en/latest/


System Requirements
-------------------

  * Python 2.7+
  * npm
    - lessc (must be installed globally, i.e. with "-g" option)
  * redis
  * LDAP
