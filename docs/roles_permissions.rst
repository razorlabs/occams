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
manager          Manages the content of the application (i.e. sets up studies)
enterer          Can enter data
reviewer         Can review data
consumer         Can view data
member           Limited view access
==============   =================================================================================================


Permissions
############

Studies
*******
``/studies``

========  =============  =======  =======  ========  ========  ======
Name      administrator  manager  enterer  reviewer  consumer  member
========  =============  =======  =======  ========  ========  ======
view      x              x        x        x         x         x
add       x              x
========  =============  =======  =======  ========  ========  ======


``/studies/595``

========  =============  =======  =======  ========  ========  ======
Name      administrator  manager  enterer  reviewer  consumer  member
========  =============  =======  =======  ========  ========  ======
view      x              x        x        x         x         x
edit      x              x
delete    x              x
========  =============  =======  =======  ========  ========  ======

Patients
********
``/patients``

========  =============  =======  =======  ========  ========  ======
Name      administrator  manager  enterer  reviewer  consumer  member
========  =============  =======  =======  ========  ========  ======
view      x              x        s        s         s         s
add       x              x        s
========  =============  =======  =======  ========  ========  ======


``/patients/xxx-xxx``

========  =============  =======  =======  ========  ========  ======
Name      administrator  manager  enterer  reviewer  consumer  member
========  =============  =======  =======  ========  ========  ======
view      x              x        s        s         s         s
edit      x              x        s
delete    x              x
========  =============  =======  =======  ========  ========  ======

Forms
********
``/patients/xxx-xxx/forms``

========  =============  =======  =======  ========  ========  ======
Name      administrator  manager  enterer  reviewer  consumer  member
========  =============  =======  =======  ========  ========  ======
view      x              x        s
add       x              x        s        s         s         s
========  =============  =======  =======  ========  ========  ======


``/patients/xxx-xxx/forms/123``

===========  =============  =======  =======  ========  ========  ======
Name         administrator  manager  enterer  reviewer  consumer  member
===========  =============  =======  =======  ========  ========  ======
view         x              x        s
edit         x              x
delete       x              x        s        s         s         s
transitions  x              x        ask m    s
===========  =============  =======  =======  ========  ========  ======

Enrollments
***********
``/patients/xxx-xxx/enrollments``

========  =============  =======  =======  ========  ========  ======  =======
Name      administrator  manager  enterer  reviewer  consumer  member  blinder
========  =============  =======  =======  ========  ========  ======  =======
view      x              x        s        s         s         s
add       x              x        s
========  =============  =======  =======  ========  ========  ======  =======


``/patients/xxx-xxx/enrollments/1234``

===========  =============  =======  =======  ========  ========  ======  =======
Name         administrator  manager  enterer  reviewer  consumer  member  blinder
===========  =============  =======  =======  ========  ========  ======  =======
view         x              x        s        s         s         s       s
edit         x              x        s
randomize    x              x        s
transition   x              x        s
delete       x              x
blinded      x                                                            s
===========  =============  =======  =======  ========  ========  ======  =======
