-- ----------------------
-- After the overhaul.py in this repo is run, then we run the overhaul.py in avrc.aeh.
-- 
-- The avrc.aeh.overhaul sets up context data in the clinical DB and connects it to
-- existing data in occams.datastore.
-- 
-- After *that* overhaul runs, we want to be able to verify that things aren't crazy
-- so that exporting from the EAV system that occams.datastore manages will actually work.
-- To ensure this, it would be helpful to have some "post-conditions" that we assume
-- will be true of the EAV/clinical composite.  This file holds those queries.
-- 
-- If any of the queries in this file return any results, it is a sign of a buggy
-- data migration process.
-- ----------------------

-- There should be no context keys of type 'patient' that point to non-existent
-- patient rows...
SELECT p.our
  FROM context c
    LEFT JOIN patient p ON c.key = p.id
  WHERE c.external = 'patient'
    AND p.our IS NULL
;

-- ----------------------
-- Same as with patients... no visits mentioned in context should "not exist".
SELECT v.visit_date
  FROM context c
    LEFT JOIN visit v ON c.key = v.id
  WHERE c.external = 'visit'
    AND v.visit_date IS NULL
;

-- ----------------------
-- Same as with patients and visits... enrollments mentioned in context should exist.
SELECT e.consent_date
  FROM context c
    LEFT JOIN enrollment e ON c.key = e.id
  WHERE c.external = 'enrollment'
    AND e.consent_date IS NULL
;

-- ----------------------
-- Every form/entity should have at least *some* context data.  If this had no LIMIT it
-- would throw tens of thousands of error rows before context overhaul runs, and should
-- throw ZERO after context overhaul runs...
SELECT e.name
  FROM entity e
    LEFT JOIN context c ON e.id = c.entity_id
  WHERE c.key IS NULL
  LIMIT 12
;

