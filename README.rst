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

Due to the nature of clinical trials in the demand for evolving data and the
importance of auditing, there are **two** different types of history tracking:

    Revisioning
        In an earlier incarnation of ``DataStore``, we used "delta" entries
        to keep track of schema changes over its lifetime. This proved to be
        excruciatingly painful to code with and so a new method was
        devised: **deep copying** schemata when a new schema version is
        proposed. There are then multiple benifits to having this mechanism:
        multiple forms can be in circulation as well as being unplublished
        for development, and data is now directly linked to the form revision
        that it was filled out for. This also has the added benifits of the
        form actually physically existing in one atomic form as opposed to
        being sharded by deltas. Also, we use a *checksum* value for
        determining how the attribute has changed across schema revisions.
        This property is useful for reporting purposes.

        Furthermore, sub schemata and choices are also deep copied.


    Auditing
        In addition to form revisions, we also care about **how** the data itself
        has changed over time (e.g. spelling errors, misentered entry data).
        Using deep copying would be overkill in these situations since we
        ever want to look at this back history for auditing purposes and
        would actually interfere when querying for entries. So, data changes
        will be stored in a separate *auditing* table to keep track of
        data deltas over time. Thus, when a row is changed, a copy of
        the previous row is entered in the auditing table and the changes
        are then applied to the live row.


Example: Revisions
++++++++++++++++++

    This example covers the concept of schema revisions
    Note that tables have been simplified to expose the core concepts.

    :Table: ``schema``

    ====  ====  ===========
    id    name  create_date
    ====  ====  ===========
    19    foo   2010-09-01
    28    bar   2011-03-17
    56    caz   2011-08-28
    122   bar   2012-03-09
    129   foo   2012-03-09
    ====  ====  ===========

    :Table: ``attribute``

    ====  =========  ====  =======  ===========
    id    schema_id  name  title    create_date
    ====  =========  ====  =======  ===========
    17    19         x     Enter x  2010-09-01
    39    28         r     Ener r   2011-03-17
    45    28         s     Enter s  2011-03-17
    51    56         a     Enter a  2011-08-28
    51    56         b     Enter b  2011-08-28
    51    56         c     Enter c  2011-08-28
    311   122        r     Enter r  2012-03-09
    345   122        s     Enter s  2012-03-09
    394   129        x     Enter x  2012-03-09
    420   129        y     Enter y  2012-03-09
    ====  =========  ====  =======  ===========

    In this example, three distinct parents exist: ``foo``, ``bar``, and ``caz``.
    Observing ``foo`` and ``bar``, we can  see they both have two revisions.
    In the case of ``foo``, another field ``y`` was added to this revision.
    In the case of ``bar``, a spelling error was fixed. Although, in some
    institutions, this my not have been necessary as simplying updating
    the schema title for the specific revision would have sufficed. But, for
    the sake of this example, we revisioned the schema.

    Also note, that attribute names are **unique** within a schema. However,
    schema names are **not unique** as there needs to be several copies
    in circulation. From data inspection, though, we should be able to
    deduce the forms are of the same lineage because of their name.


Example: Auditing
+++++++++++++++++

    This example covers the concept of data auditing in a generic case.


    :Table: ``data``

    ====  ====  =======  =======
    id    name  value    version
    ====  ====  =======  =======
    19    foo   3.0      003
    28    bar   'stuff'  001
    ====  ====  =======  =======

    :Table: ``data_history``

    ====  ====  =======  =======
    id    name  value    version
    ====  ====  =======  =======
    19    foo   0.2      001
    19    foo   1.3      002
    22    caz   15       001
    22    caz   22       002
    22    caz   32       003
    ====  ====  =======  =======


    In this example, note that each row has a ``version`` number to indicate
    how many times it has been changed. In a separate table, previous versions
    of the row are stored for historical auditing purposes, but are not
    necessarily crucial for everyday data querying. In any case, obvering the
    ``data_history`` table, we can see all the previous values of ``foo`` as
    well as discover that ``caz`` used to exist but has since been removed
    from the live table. Note that ``id`` number are what indicate the
    uniqueness of a row, which is why it's maintained in the ``data_history``
    table across all row versions.


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
    Removes the object entirely.
retire
    Retires an object (can be restored)
restore
    Restores a retired object.
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
