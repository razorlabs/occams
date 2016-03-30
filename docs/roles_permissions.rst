***********************
Roles and Permissions
***********************

Mission
#######
Manages patients, visits, and studies and their form entries.

Enrollment Numbers
###################
Used differently per institution. Need to ask how they are using it for the questions they have.


Roles
################

==============   =================================================================================================
Name             Comment
==============   =================================================================================================
administrator    Complete access to all functionality of the application. Few people should have this level.
manager          Manages the content of the application (i.e. sets up studies), Cannot review.
coordinator      Manages site-specific content
enterer          Can enter data
reviewer         Can review data
consumer         Can view data
member           Limited view access
==============   =================================================================================================


Permissions
############

X = Any Site
S = Site-specific

Studies
*******
``/studies``

==============  ====  ===
Name            view  add
==============  ====  ===
administrator   X     X
manager         X     X
coordinator     X
enterer         X
reviewer        X
consumer        X
member          X
==============  ====  ===


``/studies/595``

==============  ====  ====  ======
Name            view  edit  delete
==============  ====  ====  ======
administrator   X     X     X
manager         X     X     X
coordinator     X
enterer         X
reviewer        X
consumer        X
member          X
==============  ====  ====  ======

Cycles
******
``/studies/595/cycles``

==============  ====  ===
name            view  add
==============  ====  ===
administrator   X     X
manager         X     X
coordinator     X
enterer         X
reviewer        X
consumer        X
member          X
==============  ====  ===

``/studies/595/cycles/week-1``

==============  ====  ====  ======
name            view  edit  delete
==============  ====  ====  ======
administrator   X     X     X
manager         X     X     X
coordinator     X
enterer         X
reviewer        X
consumer        X
member          X
==============  ====  ====  ======

Patients
********
``/patients``

==============  ====  ===
Name            view  add
==============  ====  ===
administrator   X     X
manager         X     X
coordinator     S     S
enterer         S     S
reviewer        S
consumer        S
member          S
==============  ====  ===


``/patients/xxx-xxx``

==============  ====  ====  ======
Name            view  edit  delete
==============  ====  ====  ======
administrator   X     X     X
manager         X     X     X
coordinator     S     S     S
enterer         S     S
reviewer        S
consumer        S
member          S
==============  ====  ====  ======

Forms
********
``/patients/xxx-xxx/forms``

==============  ====  ===
Name            view  add
==============  ====  ===
administrator   X     X
manager         X     X
coordinator     S     S
enterer         S     S
reviewer        S
consumer        S
member          S
==============  ====  ===


``/patients/xxx-xxx/forms/123``

==============  ====  ====  ======  ================
Name            view  edit  delete  transition
==============  ====  ====  ======  ================
administrator   X     X     X       X
manager         X     X     X       X
coordinator     S     S     S       Automated
enterer         S     S             Automated
reviewer        S                   S
consumer        S
member          S
==============  ====  ====  ======  ================

Enrollments
***********
``/patients/xxx-xxx/enrollments``

==============  ====  ===
Name            view  add
==============  ====  ===
administrator   X     X
manager         X     X
coordinator     S     S
enterer         S     S
reviewer        S
consumer        S
member          S
blinder
==============  ====  ===

``/patients/xxx-xxx/enrollments/1234``

==============  ====  ====  ======  =========  =========
Name            view  edit  delete  randomize  terminate
==============  ====  ====  ======  =========  =========
administrator   X     X     X       X          X
manager         X     X     X       X          X
coordinator     S     S     S       S          S
enterer         S     S             S          S
reviewer        S
consumer        S
member          S
==============  ====  ====  ======  =========  =========  =======

Visits
******
``/studies/patients/xxx-xxx/visits``

==============  ====  ===
name            view  add
==============  ====  ===
administrator   X     X
manager         X     X
coordinator     S     S
enterer         S     S
reviewer        S
consumer        S
member          S
==============  ====  ===

``/studies/patients/xxx-xxx/visits/12345``

==============  ====  ====  ======
name            view  edit  delete
==============  ====  ====  ======
administrator   X     X     X
manager         X     X     X
coordinator     S     S     S
enterer         S     S
reviewer        S
consumer        S
member          S
==============  ====  ====  ======

``/studies/patients/xxx-xxx/visits/12345/forms``

==============  ====  ===  ======
name            view  add  delete
==============  ====  ===  ======
administrator   X     X     X
manager         X     X     X
coordinator     S     S     S
enterer         S     S
reviewer        S
consumer        S
member          S
==============  ====  ===  ======

``/studies/patients/xxx-xxx/visits/12345/forms/9999``

==============  ====  ====  ==========
name            view  edit  transition
==============  ====  ====  ==========
administrator   X     X     X
manager         X     X     X
coordinator     S     S     Automated
enterer         S     S     Automated
reviewer        S           S
consumer        S
member          S
==============  ====  ====  ==========

Exports
*******
``/studies/exports/faq|overview|checkout|cookbook``

==============  ====  ===
name            view  add
==============  ====  ===
administrator   X     X
manager         X     X
coordinator
enterer
reviewer
consumer        X     X
member
==============  ====  ===

``/studies/exports/12345``

==============  ======  ======
name            view    delete
==============  ======  ======
administrator   Owner   Owner
manager         Owner   Owner
coordinator
enterer
reviewer
consumer        Owner   Owner
member
==============  ======  ======

