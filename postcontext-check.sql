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

-- This now only detects forms where the patient data was deleted and the forms haven't
-- been.  This is organizationally complicated.  The forms will not be deleted at this
-- time but are likely to in the future, thus this SQL is likely to become useful as an
-- ongoing QA process (verifying integrity of form-to-clinical connections) in the 
-- future.  When that issue has been resolved, use these queries for that :)
-- 
-- -- ----------------------
-- -- Every form/entity should have at least *some* context data.  If this had no LIMIT it
-- -- would throw tens of thousands of error rows before context overhaul runs, and should
-- -- throw ZERO after context overhaul runs...
-- SELECT sc.name, COUNT(*)
--   FROM entity e
--     JOIN schema sc ON sc.id = e.schema_id
--     LEFT JOIN context c ON e.id = c.entity_id
--   WHERE c.key IS NULL
--     AND NOT sc.is_inline
--   GROUP BY sc.name
--   HAVING COUNT(*) > 0
--   ORDER BY COUNT(*) DESC
-- 
-- SEMICOLON NEEDED!
-- 
-- -- ----------------------
-- -- Every form/entity, more specifically, should be associated with a A PATIENT
-- -- except perhaps for Partner's where index patient import logic was a bit
-- -- tricky (data is preserved, you get the index patient via JOIN through partner)
-- SELECT sc.name, COUNT(*)
--   FROM entity e
--     JOIN schema sc ON sc.id = e.schema_id
--     LEFT JOIN context c ON (e.id = c.entity_id AND c.external = 'patient')
--   WHERE c.key IS NULL
--     -- AND sc.name NOT LIKE '%Partner%'
--     AND NOT sc.is_inline
--   GROUP BY sc.name
--   HAVING COUNT(*) > 0
--   ORDER BY COUNT(*) DESC
-- 
-- SEMICOLON NEEDED!
-- 
SELECT * FROM context WHERE 1=2;






