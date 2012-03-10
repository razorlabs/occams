==========
Change Log
==========

-----------
0.6.0 (???)
-----------

Overhauled versioning mechanics for better sanity (using deep copy method)

Credit to ``[RodriguezMueller]`` for this amazing breakthrough.

- Managers
    - ``retire``, ``restore`` are now deprecated and removed
    - ``purge`` has been renamed to ``remove``
    - ``key`` paramter may now be a specific id number of an item as opposed
            to simply it's string name
    - ``put`` **ONLY** accepts sqlalchemy items.
    - ``get`` now returns **ONLY** sqlalchemy items. If you wish to use
            the zope functionality, use the new compatibility interfaces

- Database
    - ``asOf`` removed since it requires extra control of what entries to
        return as of the specified date, the logic for this method
        has been embedded into the managers.
    - All ``*_user_id`` metadata columns are active
    - All ``remove_*`` columns have been deprecated and removed, since they
        introduce intricate dependencies with parent items that are ambiguous.
        (e.g. my parent is "retired", am I retired?)
    - ``Schema.state`` to determine its circulation, which
            will make it helpful when editing unpublished schemat
    - ``Schema.is_inline`` now indicates if the schema can only be used
            as a subschema
    - ``Attribute.min`` removed
    - ``Attribute.max`` removed
    - ``Attribute.default`` removed
    - ``Attribute.widget`` removed
    - ``Attribute.is_inline_object`` removed
    - ``Attribute.is_readonly`` removed
    - ``Attribute.checksum`` is a new property for determining the similarity
            of this attribute from another form version's
    - ``Attribute.validator`` is now observed
    - ``Attribute.value_min`` now specifies the minimum allowed length or value
    - ``Attribute.value_max`` now specifies the maximum allowed length or value
    - ``Attribute.collection_min`` now specifies the minimum length of the collection
    - ``Attribute.collection_max`` now specifies the maximum length of the collection
    - ``Entity.state`` is now a built-in column instead of a foreign key,
            as other products expect specific values of this property and should
            not be changed unless a software update is necessary
    - ``State`` deprecated in favor of new ``Entity.state`` property
    - ``User`` a new table for tracking user changes
    - ``Log`` a new table that lists specific changes to properties of
            tables, useful for displaying feeds and auditing purposes


-----------
0.5.0 (???)
-----------

- General
    - Add support for collect_date (backwards compatible)


------------------------------------
0.4.4 (2012-02-28) [Project: Editor]
------------------------------------

- General
    - Upgraded types vocabulary with titles
    - Removes widgets support
    - Using schema name instead of id for history
    - Choices now return their proper typed-value
    - Added checks to prevent adding empty stringed descriptions.
    - Zero-indexed all ordering


------------------
0.4.2 (2011-08-25)
------------------

- General
    - Fixed ON DELETE settings for value tables to cascade properly.


------------------
0.4.1 (2011-08-16)
------------------

- General
    - Disabled default values, they were causing complications with data entry.
    - Fixed: base_schema not being imported correctly.


------------------
0.4.0 (2011-07-29)
------------------

*Goal*: History support.

- General
    - Rebranded package as *DataStore* (from ``Datastore``)
    - Form/Data history functionality implemented.
    - Now includes comprehensive unit testing suite.
    - All managers now adopt the zope adapter paradigm. This means that
        ``getUtlity`` calls have been removed from the source code. Most notably,
        ``DataStore`` only takes a ``ScopedSession`` instance (as opposed to a
        string)
    - Removed dependency on ``z3c.saconfig``
    - Manager specifications updated with time-based parameters (for history)
    - Removed dependencies on zope/plone UI-specific components such as
        ``z3c.form``, ``plone.dexterity``, ``plone.autoform`` etc. The reason
        for this change is to  make DataStore it's own stand-alone utility that
        can be used command line or as a plug-in in to other frameworks. This
        approach will be further pursued in the coming versions of DataStore.

- Extensions
    - Clinical-based components moved to their own packages.

- Form
    - New form paradigm adopted: fieldsets are considered inline objects (
        or subforms, whichever way you prefer to look at it). This removes
        the heavy dependence on `plone.autoform` and instead allows for
        rich annotation of the form without the dependence of Zope-specific
        UI elements.
    - Widgets will be deprecated in a later version
    - Created new form directives (rather than using embedded
        ``zope.schema.Attribute`` instances)
    - Added batching facilities

- Database
    - Uses ``sqlalchemy.types.Enum`` for simple selection values in tables
        (such as type or class storage type)
    - Floats have been converted to Decimal type (to control precision)
    - Choices are now direct constraints of the Attribute.
    - Overhauled model structures with standard attributes such as
        ``name``/``title``/``description``/``create_date``/``modify_date``/
        ``remove_date``
    - ``Instance`` object names renamed to ``Entity``
    - Time-typed values no longer supported (only Datetime or Date)
    - Infrastructure changed to support for user changes (paper-trail)
    - Infrastructure changed to support external resource objects storage type.
    - Infrastructure changed to support external table storage type.
