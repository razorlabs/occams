===========
OCCAMS Form
===========

A tool for managing dynamic forms in Plone.


---------
Rationale
---------

As part of the OCCAMS suite of components, a method for accessing and managing
forms through the web is needed for patient data.

-----
Goals
-----

Some goals of this product:

    * Handle form entry
    * Facilitate form manipulation
    * Show form statistics (usage, # instances, % entered, states)
    * Form importing/exporting

--------------
Implementation
--------------

DataStore
+++++++++

OCCAMS Form uses DataStore as its foundation and provides a user interface for
intercting with forms through the web.


PostgreSQL
++++++++++

Currently we only support PostgreSQL

------------
Installation
------------

To install, refer  to this plugin in your egg's ``setup.py`` file::

   setup(
       name='your.awesome.project',
       # Your conifguration ...
       install_requires=[
           # Other dependencies ...
           'occams.form'
           ],
       ...
       )


Note that this product relies on z3c.saconfig_ for it's database session
source. Therefore, you must register your session components in either your
own product or plone's ZCML. Best practices would suggest you do the latter
via buildout::

    [instance]
    recipe = plone.recipe.zope2instance
    ...
    zcml-additional =
    <configure
        xmlns="http://namespaces.zope.org/zope"
        xmlns:db="http://namespaces.zope.org/db">
      <include package="z3c.saconfig" file="meta.zcml" />
      <db:engine name="YOUR.OWN.ENGINE" url="postgresql://...." />
      <db:session name="YOUR.OWN.SESSION" engine="YOUR.OWN.ENGINE" />
    </configure>
    
This will help keep all your connections in one file as opposed to having them
scattered through out your eggs, and additionaly it will prevent your from
accidentally commiting your configuration details to your SCM!

Once installed, you will be able to select from a list of registered
``z3c.saconfig`` sessions as the target form repository.

.. z3c.saconfig: http://pypi.python.org/pypi/z3c.saconfig

------------
Attributions
------------

Some icons by `Yusuke Kamiyamane`_. All rights reserved. Licensed under a `Creative Commons Attribution 3.0`_

.. _Yusuke Kamiyamane: http://p.yusukekamiyamane.com/
.. _Creative Commons Attribution 3.0: http://creativecommons.org/licenses/by/3.0/


----------
Disclaimer
----------

This product may contain traces of nuts.


------------------
Self-Certification
------------------

    [ ] Internationalized

    [ ] Unit tests

    [ ] End-user documentation

    [ ] Internal documentation (documentation, interfaces, etc.)

    [ ] Existed and maintained for at least 6 months

    [ ] Installs and uninstalls cleanly

    [ ] Code structure follows best practice
