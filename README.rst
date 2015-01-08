OCCAMS Form
===========

A web application for managing dynamic forms.


Rationale
---------

As part of the OCCAMS suite of components, a method for accessing and managing
forms through the web is needed for patient data.

Goals
-----

Some goals of this product:

    * Handle form entry
    * Facilitate form manipulation
    * Show form statistics (usage, # instances, % entered, states)
    * Form importing/exporting

Implementation
--------------

DataStore
+++++++++

OCCAMS Form uses DataStore as its foundation and provides a user interface for
intercting with forms through the web.


PostgreSQL
++++++++++

Currently we only support PostgreSQL

Installation
------------

Python
++++++
To install, refer  to this plugin in your egg's ``setup.py`` file::

   setup(
       name='your.awesome.project',
       # Your conifguration ...
       install_requires=[
           # Other dependencies ...
           'occams.forms'
           ],
       ...
       )


Node Packages
+++++++++++++

This project depends on some node package for asset-dependency management::

  cd /path/to/occams.forms
  npm install
  ./node_modules/.bin/bower install


Authentication
++++++++++++++

Because many organizations have their politics of authentication, this app
tries to not force any authentication paradigm on the client and instead
uses `repoze.who` to allow clients to supply their own authentication via
customized-organization-specific plugins.


Credits
------------

This addon uses icons from various sources, which are credited below:

**Silk Icons**

`Mark James (FamFamFam)`_. All rights reserved. Licensed under `Creative Commons Attribution 3.0`_

**Silk Icons Companion**

`Damien Guard`_. All rights reserved. Licensed under `Creative Commons Attribution 3.0`_

**Fugue Icons**

`Yusuke Kamiyamane`_. All rights reserved. Licensed under `Creative Commons Attribution 3.0`_

.. _Damien Guard: http://damieng.com/creative/icons/silk-companion-1-icons
.. _Mark James (FamFamFam): http://www.famfamfam.com/lab/icons/silk/
.. _Yusuke Kamiyamane: http://p.yusukekamiyamane.com/
.. _Creative Commons Attribution 3.0: http://creativecommons.org/licenses/by/3.0/


Self-Certification
------------------

    [ ] Internationalized

    [ ] Unit tests

    [ ] End-user documentation

    [ ] Internal documentation (documentation, interfaces, etc.)

    [ ] Existed and maintained for at least 6 months

    [ ] Installs and uninstalls cleanly

    [ ] Code structure follows best practice
