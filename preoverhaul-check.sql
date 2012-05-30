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

