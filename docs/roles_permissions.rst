***********************
Roles and Permissions
***********************

Mission
#######
Allow users to manage form schemata and workflows.


Roles
######

==============   ==========================================
Name             Comment
==============   ==========================================
member           Limited view access
admin            All permissions
manager          Coordinates form and workflow management
editor           Edits forms
==============   ==========================================

Permission Descriptions
#######################

================      =======================================================
Name                  Comment
================      =======================================================
admin                 Can perform dangerous administrative actions.
form_add              Can create new forms by drafting/uploading/adding
form_amend            Can make changes to a published form without versioning
form_delete           Can delete forms with no data
form_edit             Can make changes to unpublished forms
form_publish          Can publish a form
form_retract          Can retract a form
form_view             Can view/preview forms
workflow_add          Can create a new workflow
workflow_delete       Can delete a workflow
workflow_edit         Can edit workflow map
workflow_view         Can view workflow map
================      =======================================================

Permissions
############
================      ==============  ========  =======  =======
Name                  administrator   manager   editor   member
================      ==============  ========  =======  =======
admin                 X
form_add              X               X         X
form_amend            X               X
form_delete           X               X         X
form_edit             X               X         X
form_publish          X               X         X
form_retract          X               X
form_view             X               X         X        X
workflow_add          X               X
workflow_delete       X               X
workflow_edit         X               X
workflow_view         X               X         X        X
================      ==============  ========  =======  =======

Forms
*******
``/forms``

==============  ====  ====  ===  ======
Name            view  edit  add  delete
==============  ====  ====  ===  ======
administrator   X     X     X    x
manager         X     X     X    X
editor          X     *     X    *
member          X
==============  ====  ====  ===  ======

* editor may edit or delete only when the form is not published

``/forms/{form}/versions/{version}``

==============  ====  ====  ===  ======
Name            view  edit  add  delete
==============  ====  ====  ===  ======
administrator   X     X     X    x
manager         X     X     X    X
editor          X     *     X
member          X
==============  ====  ====  ===  ======

* editor may edit only when the form is not published

``/forms/{form}/versions/{version}/editor``

==============  ====
Name            edit
==============  ====
administrator   X
manager         X
editor          *
member
==============  ====

* editor may edit only when the form is not published

``/forms/{form}/versions/{version}/preview``

==============  ====
Name            view
==============  ====
administrator   X
manager         X
editor          X
member          X
==============  ====
* editor may edit or delete only when the form is not published

``/forms/{form}/versions/{version}/fields``

==============  ====  ====  ===
Name            view  edit  add
==============  ====  ====  ===
administrator   X     X     X
manager         X     X     X
editor          X     X     X
member          X
==============  ====  ====  ===

``/forms/{form}/versions/{version}/fields/{field}``

==============  ====  ====  ======
Name            view  edit  Delete
==============  ====  ====  ======
administrator   X     X     x
manager         X     X     X
editor          X     *     *
member          X
==============  ====  ====  ======

* editor may edit or delete only when the form is not published

``/forms/workflows/default``

==============  ====
Name            view
==============  ====
administrator   X
manager         X
editor          X
member          X
==============  ====
