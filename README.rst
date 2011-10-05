=========
DataStore
=========


The purpose of this plug-in is to facilitate the management of sparse data that
is changing over time, namely clinical trials data.


----------------------------
Entity-Attribute-Value (EAV)
----------------------------

This system employs a database framework known as
`Entity-Attribute-Value with Schema-Relationships` or simply `EAV`_ for
short.

.. _EAV: http://www.ncbi.nlm.nih.gov/pmc/articles/PMC61391/

Using this setup, new object schema can be dynamically defined to allow new
attributes to be entered for an entity.

Example: Basic EAV schema definition and usage primer.
++++++++++++++++++++++++++++++++++++++++++++++++++++++

    :Table: ``schema``

    ====  ====
    id    name
    ====  ====
    13    Foo
    ====  ====

    :Table: ``attribute``

    ====  =========  =====  ========
    id    schema_id  name   type
    ====  =========  =====  ========
    11    13         bar    string
    15    13         rar    string
    23    13         baz    integer
    24    13         lio    decimal
    37    13         caz    datetime
    ====  =========  =====  ========

    The ``schema`` and ``attribute`` tables show a simple case of how
    a schema definition would be stored in this system. In this case schema
    ``Foo`` has five attributes each with their own data-type whose
    values are then stored in their own type-specific table:

    :Table: ``entity``

    ====  =========  ==========
    id    schema_id  name
    ====  =========  ==========
    55    13         foo_object
    ====  =========  ==========

    :Table: ``string``

    ====  ============  =============
    id    attribute_id  value
    ====  ============  =============
    38    13            'Hello World'
    38    15            'Huzzah'
    ====  ============  =============

    :Table: ``integer``

    ====  ============  =============
    id    attribute_id  value
    ====  ============  =============
    38    23            420
    ====  ============  =============

    :Table: ``decimal``

    ====  ============  =============
    id    attribute_id  value
    ====  ============  =============
    38    24            98.7
    ====  ============  =============

    :Table: ``datetime``

    ====  ============  =============
    id    attribute_id  value
    ====  ============  =============
    38    37            2012-12-21
    ====  ============  =============

    Of course, the actual implementation of the above data tables is
    more complex, these examples serve as a primer on the basics of how
    the sparse data is stored.

----------------
History Tracking
----------------

Because a clinical trial is evolving throughout its life cycle, data schema
should be able to accommodate those changes. Enter **history tracking**

History tracking is accomplished in the database framework by using the entrie's
``name`` field throughout it's life cycle and simply marking the entry as
removed when a new version is to be commissioned.


Example: Active/Retired
+++++++++++++++++++++++

    :Table: ``sample``

    ====  ====  ===========  ===========
    id    name  create_date  remove_date
    ====  ====  ===========  ===========
    28    foo   2011-06-07   2011-06-08
    45    foo   2011-06-08   2011-07-25
    57    foo   2011-08-10
    ====  ====  ===========  ===========

    In the above example we see that the object named ``foo`` was added on
    ``2011-06-07`` and retired a couple of times. In the last row it was
    inactive for a couple of weeks before being active again. Note that the last
    column does not have a ``remove_date`` because it is the currently active
    version of the ``foo`` object.


Although this paradigm is fairly simple for objects that don't have any
dependents, it because increasingly complex when the object must then
be referenced other objects.


Example: With child objects
+++++++++++++++++++++++++++

    We now look at another example where an object can have children and how
    it affects history tracking.

    :Table: ``parent``

    ====  ====  ===========  ===========
    id    name  create_date  remove_date
    ====  ====  ===========  ===========
    28    foo   2011-03-17
    ====  ====  ===========  ===========

    :Table: ``child``

    ====  =========  ====  ===========  ===========
    id    parent_id  name  create_date  remove_date
    ====  =========  ====  ===========  ===========
    17    28         bar   2011-03-27   2011-05-20
    24    28         bar   2011-05-25   2011-06-03
    33    28         bar   2011-07-01
    ====  =========  ====  ===========  ===========

    In this example, the child ``bar`` has a parent ``foo``. The child entry
    was modified several times during the life cycle of ``foo`` and is
    active as of ``2011-08-10``.

    In this particular case, the parent object inherently has several versions
    based on the revisions done to it's child that must be taken into
    account. Thus, the parent ``foo`` should have the following versions:

        - 2011-03-17 (Date ``foo`` was added)
        - 2011-03-25 (Date ``bar`` was added)
        - 2011-05-20 (Date ``bar`` was updated)
        - 2011-06-03 (Date ``bar`` was retired)
        - 2011-07-01 (Date ``bar`` was activated)


Example: Multi-versioned parent with multi-versioned children
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    We now look at an extreme example similar to what would be found in a
    typical use case.

    :Table: ``parent``

    ====  ====  ===========  ===========
    id    name  create_date  remove_date
    ====  ====  ===========  ===========
    28    foo   2011-03-17   2011-05-25
    45    foo   2011-05-25   2011-06-13
    57    foo   2011-07-01
    ====  ====  ===========  ===========

    :Table: ``child``

    ====  =========  ====  ===========  ===========
    id    parent_id  name  create_date  remove_date
    ====  =========  ====  ===========  ===========
    17    28         bar   2011-03-27
    19    28         lio   2011-03-27
    24    45         bar   2011-05-25
    28    45         lio   2011-05-25   2011-05-29
    33    57         bar   2011-07-01
    ====  =========  ====  ===========  ===========

    In this example, the parent ``foo` was revised several times and so its
    children where also copied with each revision. Note that child ``lio`` was
    removed before the the third revision of parent ``foo``. Of particular
    importance in this example is that the child objects inherit the the removal
    dates of their parents, unless otherwise noted.


In this context of EAV, data is entered into the current version of the schema
(i.e. no backversion data entry is allowed).

Some of the limitations of this approach, however, is the fact that data
must be copied with each revision, as well as possible name collisions that may
interfere with the timestamps. One final limitation is the the increase in
complexity of query-writing to an already complicated data design (EAV query
writing).


--------
Managers
--------

Managers are a way to access the DataStore data through a Python API that
mimics a container-like system.

Basic manager terminology is defined as follows:

keys
    Lists the names.
lifecycles
    Lists the revisions of a name.
has
    Checks if the name exists.
purge
    Retires an object (can be restored)
retire
    Removes the object entirely.
restore
    Restores a purged object.
put
    Add/Edit an object
get
    Retrieve an object.

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
