==========
Change Log
==========


-----------------------------
2.0.0 (2014-03-31 [Reporting]
-----------------------------

*Goal*: Production-ready reporting

- General
    - Upgraded reporting module to the following rendering options:
        - Split collections: Split multiple choice to one column per possible
            answer choice
        - Use choice labels: Uses human-readable choice labels instead of codes
        - Ignore private: de-identifies private data
        - BY_NAME is the only behavior moving forward, BY_ID and BY_CHECKSUM
            are just too confusing for the analysts
    - XML Schema import/export removed in favor of JSON
    - Schema/Attribute can no longer be accessed like dictionaries, please use
        the ``attributes``/``sections``/``choices`` properties

- Managers
  - Removed in favor of query the models directly

- Database
  - Added new ``choice`` datatype speciccally for singly/multi choice questions
  - Removed ``object`` type as it is extremely difficult  and slow to generate
      queries. All sub-objects and sub-schemata have been flattened.
  - Added new ``section`` table to assist with visual subform-rendering.


-------------------
1.0.0a (2012-06-14)
-------------------

- General
    - Rebranded to ``occams.datastore``
    - Overhauled versioning mechanics to new "cabinet" anology
    - Auditing enabled
    - XML module for export/import schemata
    - 100% code testing coverage
    - Switched to alembic database migration system

- Managers
    - Deprecated, query the models directly

- Database
    - ``asOf`` removed since it requires extra control of which entries to
        return as of the specified date, the logic for this method
        has been embedded into the managers.
    - All ``*_user_id`` metadata columns are activated
    - All ``remove_*`` columns have been removed, since they introduce complicated
        dependencies with parent items that are ambiguous.
        (e.g. my parent is "retired", am I retired?)
    - ``Schema.state`` to determine its circulation, which will make it helpful
        when editing unpublished schemat
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
    - ``State`` removed in favor of new ``Entity.state`` property
    - ``User`` a new mapping for tracking user changes
    - ``Context`` a new mapping for relating entities to external resources
    - ``External`` a new mapping for keeping track of external resources
    - ``Category`` a new mapping for tagging forms rather than creating subclasses.


------------------
0.5.0 (2012-03-20)
------------------

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
