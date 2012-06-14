-- ----------------------
-- We need to patch buggy data before fixing the data...
-- THIS collection of SQL detects issues before, and verifies fixes after.
-- The OTHER SQL should be run in the middle to do the fixing.


-- ----------------------

-- Some weird choice attributes have messed up dates.  Fix and verify the fix!

-- There are other attributes for other forms that have weird choice/date issues
-- but this SHOWS the ones to fix to make a problem go away:
--   -- AND attribute.id IN (271,272,274,308,309,310,311,273)
SELECT sc.name, sc.create_date, a.name, a.id, a.create_date, sc.create_date - a.create_date AS time_diff
  FROM schema sc
    JOIN attribute a ON a.schema_id = sc.id
  WHERE sc.name IN ('FollowupHistoryNeedleSharingPartners','IEarlyTestMSMPartners')
    AND a.create_date - sc.create_date > (interval '3 days')
;
-- ----------------------

-- Two RapidTests are confused because of a create_date on the 
-- *morning* before the RapidTest was versioned (in a tricky
-- way) later that day...
-- THIS query shows the two problems on a naive DB:
SELECT e.name, e.create_date, sc.name, sc.create_date
  FROM entity e
    JOIN schema sc ON e.schema_id = sc.id
  WHERE DATE(e.create_date) = '2012-03-01'
    AND e.create_date < '2012-03-01 13:13:45.198454'
    AND sc.name = 'RapidTest' -- e.schema_id IN (19,75)
;

-- ----------------------

-- Precondition #5 for overhaul.py is that the source schema table is
-- unique on (schema.name,DATE(create_date)).  Make sure that's true:

SELECT name, DATE(create_date), COUNT(*)
  FROM schema
  GROUP BY name, DATE(create_date)
  HAVING COUNT(*) > 1
;

-- ----------------------

-- There are some visit-associated forms that are associated
-- with more than one visit in the original data, which is logically
-- impossible in the new system.  
-- This SHOWS the problem children:
SELECT e.name
      ,COUNT(DISTINCT(vi.visit_id)) as visit_count
      ,array_agg(DISTINCT(vi.visit_id)) as visit_ids
      ,bool_or(e.remove_date IS NULL) as has_any_live
  FROM entity e
    JOIN visit_instance vi ON e.id = vi.instance_id
  GROUP BY e.name
  HAVING COUNT(DISTINCT(vi.visit_id)) > 1 -- confusing duplicates...
     AND bool_or(e.remove_date IS NULL) -- ...that matter because some are live
;

-- ----------------------

-- The original protocol/cycle table represents planned steps within
-- a study.  It will change names from "protocol" to "cycle".  Before
-- the transition, a duplication (two things with the same "NAME") 
-- need to be patched so that the spurious one is gone.

-- This query SHOWS duplication, specifically for p_ids = {25,26}
SELECT domain_id, cycle, COUNT(*), array_agg(id) as ids
  FROM protocol
  GROUP BY domain_id, cycle
  HAVING COUNT(*) > 1
;

-- This query SHOWS references to p_id=25 that should be redirected:
SELECT protocol_id, 'visit_protocol' as table_src
  FROM visit_protocol
  WHERE protocol_id = 25
UNION ALL
SELECT protocol_id, 'specimen' as table_src
  FROM specimen
  WHERE protocol_id = 25
UNION ALL
SELECT protocol_id, 'protocol_schema' as table_src
  FROM protocol_schema
  WHERE protocol_id = 25
;

-- ----------------------

-- The Termination form versioned in the old-versioning system to get
-- a new 'screen-failure' option, and then old data was marked as
-- having that problem.  In the new system, that violates the constraint
-- of "writing on paper that didn't exist then" issue.  Solution to make
-- things happen is to sneak a new choice in there.

-- This SHOWS the problem:
SELECT sc.id, sc.name
  FROM schema sc
    JOIN attribute a ON sc.id = a.schema_id
  WHERE a.name = 'reason'
    AND 'screen-failure' NOT IN (
      SELECT ch.value
        FROM choice ch
        WHERE ch.attribute_id = a.id)
;

-- ----------------------

-- Gary had result Positive changed to Preliminary Positive and verify_results 
-- Negative to Discordant. This has been generally unhappy-making for data users
-- and now we're having schema/date constraint issues trying to migrate it.  The
-- current plan is to detect and adjust the past Gary-suggested-values so that
-- just "never existed" and thus to make things easier to import.  Cross fingers!

-- This SHOWS the RapidTests.result = prelim positive in the choice tables
SELECT sc.id, sc.name, a.create_date, a.name, v.create_date, v.value, v.id AS choice_id
  FROM choice v
    JOIN attribute a ON a.id = v.attribute_id
    JOIN schema sc   ON sc.id = a.schema_id
  WHERE v.value = 'Preliminary Positive'
    AND sc.name = 'RapidTest'
    AND a.name = 'result'
;

-- This SHOWS the RapidTests.result = prelim positive in the string tables
SELECT sc.id AS schema_id, e.create_date, e.name, v.create_date, v.value
  FROM string v
    JOIN entity e    ON e.id = v.entity_id
    JOIN schema sc   ON sc.id = e.schema_id
  WHERE v.value = 'Preliminary Positive'
    AND sc.name = 'RapidTest'
;

-- This SHOWS the RapidTests.verify_result = discordant in the choice tables
SELECT sc.id, sc.name, a.create_date, a.name, v.create_date, v.value, v.id AS choice_id
  FROM choice v
    JOIN attribute a ON a.id = v.attribute_id
    JOIN schema sc   ON sc.id = a.schema_id
  WHERE v.value = 'Discordant'
    AND sc.name = 'RapidTest'
    AND a.name = 'verify_result'
;

-- This SHOWS the RapidTests.result = prelim positive in the string tables
SELECT sc.id AS schema_id, e.create_date, e.name, v.create_date, v.value
  FROM string v
    JOIN entity e    ON e.id = v.entity_id
    JOIN schema sc   ON sc.id = e.schema_id
  WHERE v.value = 'Discordant'
    AND sc.name = 'RapidTest'
;

