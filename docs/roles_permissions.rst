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
######

================  ================================================================================================
Name              Comment
================  ================================================================================================
administrator     Complete access to all functionality of the application. Few people should have this level.
investigator
manager           Manages the content of the application (i.e. sets up studies)
analyst           Can access restricted data for report processing.
nurse             Collects forms
assistant
student           Can collect forms but only see the ones he/she has created
member            Limited view access
================  ================================================================================================

Proposed Roles
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

Permission Descriptions
#######################

====================  =======================================================
Name                  Comment
====================  =======================================================
admin                 Can perform dangerous administrative actions
export                Can export de-identified data
fia_view              Can view non-private form entries
fia_add               Can add non-private form entries
fia_edit              Can edit non-private form entries
fia_delete            Can delete non-private form entries
phi_view              Can view patient’s private form entries
phi_add               Can add patient’s private form entries
phi_edit              Can edit patient’s private form entries
phi_delete            Can delete patient’s private form entries
study_view
study_add
study_edit
study_delete
cycle_view
cycle_add
cycle_edit
cycle_delete
site_view
site_add
site_edit
site_delete
patient_view
patient_add
patient_edit
patient_delete
enrollment_view
enrollment_add
enrollment_edit
enrollment_delete
enrollment_randomize
visit_view
visit_add
visit_edit
visit_delete
====================  =======================================================

Permissions
############
====================  =====  ======  ===  =======  ===  ======  ===  ===
Name                  admin  invest  man  analyst  nur  assist  stu  mem
====================  =====  ======  ===  =======  ===  ======  ===  ===
admin                 X
export                X      X       X    X
fia_view              X      X       X    X        X    X       X    X
fia_add               X              X
fia_edit              X              X    X        X    X       X
fia_delete            X              X    X        X    X       X
phi_view              X      X       X    X        X
phi_add               X              X    X        X
phi_edit              X              X    X        X
phi_delete            X              X    X        X
study_view            X      X       X    X        X    X       X    X
study_add             X              X
study_edit            X              X
study_delete          X              X
cycle_view            X      X       X    X        X    X       X    X
cycle_add             X              X
cycle_edit            X              X
cycle_delete          X              X
site_view             X      X       X    X        X    X       X    X
site_add              X
site_edit             X
site_delete           X
patient_view          X      X       X    X        X    X       X    X
patient_add           X              X             X    X       X
patient_edit          X              X             X    X       X
patient_delete        X              X
enrollment_view       X      X       X    X        X    X       X    X
enrollment_add        X              X             X    X       X
enrollment_edit       X              X             X    X       X
enrollment_delete     X              X
enrollment_randomize  X              X
visit_view            X      X       X    X        X    X       X    X
visit_add             X              X             X    X       X
visit_edit            X              X             X    X       X
visit_delete          X              X
====================  =============  ===  =======  ===  ======  ===  ===