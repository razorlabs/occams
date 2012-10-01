OCCAMS Roster
=============

Utility for issuing OUR numbers and keeping track of which sites they have been
distributed to.

OUR Number
----------

An OUR number (short for "Our Unique Reference") is a base 36 value that is
assigned to subjects, such as clinical patients for a particular site.

The format for these numbers is typically 3 digits followed by a dash and
another 3 digits, without any "look-alike" characters (1,l) or vowels
(to avoid offesive words)


Usage
-----

Although this product is designed to hook into the Plone/Zope platform, any
object that wants to issue OUR numbers simply needs to define a
``get_source_name`` method so that the ``OurNumberSupport`` utility can
generate an our number for it. See the ``interfaces`` module for further
details.


Installation
------------

Requires a z3c.saconfig session named ``occams.roster.Session``


==================
Self-Certification
==================

    [ ] Internationalized

    [X] Unit tests

    [ ] End-user documentation

    [X] Internal documentation (documentation, interfaces, etc.)

    [X] Existed and maintained for at least 6 months

    [ ] Installs and uninstalls cleanly

    [X] Code structure follows best practice

