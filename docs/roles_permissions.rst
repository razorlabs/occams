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