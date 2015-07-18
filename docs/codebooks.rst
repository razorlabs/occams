Codebook Specification
======================

Codebooks contain a detailed blue print of each field within eCRF.
The primary interchange format is CSV_ (comma-separated-values).

.. _CSV: https://en.wikipedia.org/wiki/Comma-separated_values


Column Format
-------------

Each row in the codebook file contains information about each question
within an eCRF as well as choice code constraints.

All questions for each version of the eCRF must appear in the file.

Below is a list of the required columns and a brief description of their
purpose:

=============== =================== ===========================================
Column Name     Example             Description
=============== =================== ===========================================
table           sample_ecrf         The system name for the eCRF, which will be
                                    used as the file name of the data file.

form            Sample eCRF         The display/printable title of the eCRF.

publish_date    2015-07-01          The version of the eCRF.
                                    Values must be in ISO-8601 format
                                    (i.e. YYYY-MM-DD)

field           myvar               The variable name of the field.

title           My Variable         The printed question for the field.

description     Long description    A longer help text for the field.(optional)

is_required     TRUE                Flag indicating that the field is required
                                    during data entry.

                                    Possible values are: TRUE or FALSE

is_system       FALSE               Flag indicating that the field is managed
                                    by the system.

                                    Possible values are: TRUE or FALSE

is_collection   FALSE               Flag indicating that the field can have
                                    multiple selections. This is only
                                    applicable to "choice" fields.

                                    Possible values are: TRUE or FALSE

is_private      TRUE                Flag indicating that the field contains
                                    sensitive subject information.

                                    Possible values are: TRUE or FALSE

type            string              The data type for the variable.

                                    Possible values are:
                                        * boolean
                                        * choice
                                        * string
                                        * text
                                        * blob
                                        * date
                                        * datetime
                                        * numeric

choices         0=No;1=Yes;2=N/A    Available answer choices for the field.
                                    This only applies to variables of
                                    type "choice".
                                    Each answer choice is a numeric code
                                    followed by an equals (=) sign followed
                                    by the displayed label, delimited by
                                    semi-colon.

                                    Please note that order is important.

order           3                   The display order of the field.
                                    Does not apply to system variables.

=============== =================== ===========================================


System Variables
----------------

In addition to the eCRF questions, the codebook must specify the system
variables to be used within the form.  These are meta data variables within
each eCRF that OCCAMS manages on behalf of the user while interacting with
the Studies application.

Currently, these are not configurable and must be specified for documentation
purposes.

The following is a brief description of the required system variables:


=================== ===============================================================
Variable            Description
=================== ===============================================================
id                  The eCRF entry's unique system identification number.
pid                 The patient identifier that the entry belongs to.
site                The patient's site string token.
enrollment          The study code this entry was collected for.
enrollment_ids      The system id of the enrollment.
visit_cycles        The visit cycle(s) this form was collected for.
                    Semi-colon separated if the entry was collected for more
                    than one study-cycle.
visit_date          The date of the visit this entry was collected.
visit_id            The system id for visit
form_name           The form system name
form_publish_date   The form version
state               The current work flow state token (e.g. pending-entry,
                    pending-review, complete)
collect_date        The user-selected date the data for the entry was collected.
                    This can differ from the visit date if the entry needs to
                    be associated with a visit but was collected at a later
                    time.
not_done            Boolean flag indicating if the entry was actually collected.
create_date         The actual date and time the entry was entered into the
                    system.
                    This value may differ from both collect_date and
                    visit_date as data may be retroactively be imported into the
                    system. OCCAMS manages this field for auditing purposes.
create_user         The user who created the entry.
modify_date         The last time this entry was modified.
                    This value may differ from both collect_date and
                    visit_date as data may be retroactively be imported into the
                    system. OCCAMS manages this field for auditing purposes.
modify_user         The last user who modified the entry.
=================== ===============================================================


The "boilerplate" system variables are as follows and must be included
for each eCRF version:

.. csv-table::
    :header: table,form,publish_date,field,title,description,is_required,is_system,is_collection,is_private,type,choices,order

    sample_ecrf,,,id,,,TRUE,TRUE,FALSE,FALSE,numeric,,
    sample_ecrf,,,pid,,,TRUE,TRUE,FALSE,FALSE,string,,
    sample_ecrf,,,site,,,TRUE,TRUE,FALSE,FALSE,string,,
    sample_ecrf,,,enrollment,,,FALSE,TRUE,TRUE,FALSE,numeric,,
    sample_ecrf,,,enrollment_ids,,,FALSE,TRUE,TRUE,FALSE,numeric,,
    sample_ecrf,,,visit_cycles,,,FALSE,TRUE,TRUE,FALSE,string,,
    sample_ecrf,,,visit_date,,,FALSE,TRUE,FALSE,FALSE,date,,
    sample_ecrf,,,visit_id,,,FALSE,TRUE,FALSE,FALSE,numeric,,
    sample_ecrf,,,form_name,,,TRUE,TRUE,FALSE,FALSE,string,,
    sample_ecrf,,,form_publish_date,,,TRUE,TRUE,FALSE,FALSE,string,,
    sample_ecrf,,,state,,,TRUE,TRUE,FALSE,FALSE,string,,
    sample_ecrf,,,collect_date,,,TRUE,TRUE,FALSE,FALSE,date,,
    sample_ecrf,,,not_done,,,TRUE,TRUE,FALSE,FALSE,boolean,,
    sample_ecrf,,,create_date,,,TRUE,TRUE,FALSE,FALSE,date,,
    sample_ecrf,,,create_user,,,TRUE,TRUE,FALSE,FALSE,string,,
    sample_ecrf,,,modify_date,,,TRUE,TRUE,FALSE,FALSE,date,,
    sample_ecrf,,,modify_user,,,TRUE,TRUE,FALSE,FALSE,string,,
