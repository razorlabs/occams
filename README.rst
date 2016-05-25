================
OCCAMS DataStore
================

.. image:: https://travis-ci.org/younglabs/occams_datastore.svg?branch=master
    :target: https://travis-ci.org/younglabs/occams_datastore
    :alt: Master Travis CI Status

.. image:: https://coveralls.io/repos/github/younglabs/occams_datastore/badge.svg?branch=master
    :target: https://coveralls.io/github/younglabs/occams_datastore?branch=master
    :alt: Coveralls.io Coverage

API and backend for managing sparse data that is changing over time,
namely clinical research data.


----------------------------
Entity-Attribute-Value (EAV)
----------------------------

This system employs a database heuristic known as
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


Versioning
++++++++++

A brief history: In an earlier incarnation of ``DataStore``, we used "delta"
entries to keep track of schema changes over its lifetime. This proved to be
excruciatingly painful to code with and so a new method was
devised: **deep copying** schemata when a new schema version is
proposed.

The general concept behind *deep-copy* follows a *cabinet analogy* that
the we devised to help explain. In this anaology, we've abstracted schemata
to paper forms and the database to a filing cabinet. Typically a form
will be drafted to collect data about a certain subject. The draft form is then
published and when data needs to be filled in, a photo copy of the form is
made to be filled out and stored into the filing cabinet. Now, say that
the there were mistakes in the form. The general procedure would be to photo
copy the form, whiteout changes, add new questions and then stick the form
back into the filing cabinet. Now we have to versions of the form in circulation
that can be further photo copied for data entry or redrafting.

There are multiple benifits to using the deep-copy mechanism:
multiple forms can be in circulation as well as being unplublished
for development, and data is now directly linked to the form revision
that it was filled out for. This also has the added benifits of the
form actually physically existing in one atomic form as opposed to
being fragmented by deltas.

Also, we use an internal *checksum* value for determining how the attribute has
changed across schema revisions. This property is useful for reporting purposes.

Furthermore, sub schemata and choices are also deep copied. This means
that a sub schemata can only really have one parent and not be shared accross
schemata.


Auditing
++++++++

In addition to form revisions, we also care about **how** the data itself
has changed over time (e.g. spelling errors, misentered entry data).
Using deep copying would be overkill in these situations since we
ever want to look at this back history for auditing purposes and
would actually interfere when querying for entries. So, data changes
will be stored in a separate *auditing* table to keep track of
data deltas over time. Thus, when a row is changed, a copy of
the previous row is entered in the auditing table and the changes
are then applied to the live row. Furthermore we keep track of who changed
the data.


Example: Schema copies
++++++++++++++++++++++

    This example covers the concept of schema deep copying.
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


------------
Requirements
------------

* PostgreSQL 9.3+
* Python 2.7+


------------
Installation
------------

Installation and setup::

> source /path/to/your/virtualenv/bin/activate
> pip install occams.datastore
> od_initdb --db postgresql://user:pw@yourhost/yourdb
> python


Starting a session::

>>> DB_URL = 'postgresql://user:pw@yourhost/yourdb'
>>>
>>> from datetime import date
>>> import sqlalchemy
>>> from sqlalchemy import orm
>>> from occams.datastore import models
>>> from occams.datastore.models.events import register
>>>
>>> engine = sqlalchemy.create_engine(DB_URL)
>>> Session = orm.scoped_session(orm.sessionmaker(bind=engine))
>>> register(Session)
>>> Session.info['blame'] = models.User(key='user@localhost')

The above initializes your own database session. The ``register`` call intializes
all the event handling callbacks (for auditing, default values, integrity checks etc).
Notice the 'blame' info data passed. This tells datastore who is the current
active user so that the auditing logic can keep track of who is responsible
for the data commits. The sample assumes the blame user has not been created yet.

Creating a schema::

>>> myfirst = models.Schema(name=u'myfirst', title=u'My First Schema', publish_date=date.today())
>>> myfirst.attributes['myvar'] = models.Attribute(name=u'myvar', title=u'Does this help?', type='choice', order=0)
>>> myfirst.attributes['myvar'].choices['0'] = models.Choice(name='0', title=u'No', order=0)
>>> myfirst.attributes['myvar'].choices['1'] = models.Choice(name='1', title=u'Yes', order=1)
>>> myfirst.attributes['myvar'].choices['3'] = models.Choice(name='3', title=u'Maybe', order=2)
>>> Session.add(myfirst)
>>> Session.flush()


Saving data against a schema::

>>> mydata = models.Entity(schema=myfirst)
>>> mydata['myvar'] = '1'
>>> Session.add(mydata)
>>> Session.flush()


Finishing your work::

>>> Session.commit()


-------------------------------------
Installation as a development package
-------------------------------------

**Make sure you USE A TESTING DATABASE to avoid corrupting your production data.**

You'll need to install as a test package and create a testing database::

> source /path/to/your/virtualenv/bin/activate
> pip install -e git+ssh://git@bitbucket.org/ucsdbitcore/occams.datastore.git@develop#egg=occams.datastore[postgresql]
> od_initdb --db postgresql://user:pw@yourhost/youttestdb

We do not create the tables in the unittests because they take too much time
to create in between testing.

Running the unit tests::

> cd /path/to/your/virtualenv/src/occams.datastore
> nosetests --tc=db:postgresql://user:pw@yourhost/youttestdb


---------------------------
Where's the user interface?
---------------------------

This module only implements the EAV system using `SQLAlchemy`_, to maintain
the implementation vendor-agnostic as much as possible. As such, much of
the functionality is integrated into the model classes so that the ORM
can be used as the API. Additionally, there is no web interface built-in as
the general goal here is to offer a generic sparse-data solution that can be
used further customized on a per-institution basis. For one such example, see
`occams.forms`_

.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _occams.form: https://bitbucket.org/ucsdbitcore/occams.forms.git
