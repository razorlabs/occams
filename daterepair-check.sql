-- ----------------------
-- We need to patch the date_collected situation once we have forms and context for them.
-- THIS collection of SQL detects issues before, and verifies fixes after.
-- The OTHER SQL should be run in the middle to do the fixing.


-- ----------------------
-- We are transitioning from a regime where entity.collect_date is built into all forms
-- and date_collected attribute (which exists for some but not all forms) is being 
-- phased out.  Also, there is a "semi-bug" (makes sense for most things but not this?)
-- in datastore that leaves entity.collect_date as the **import** time rather than
-- something sane.  We're fixing this by adjusting entity.collect_date using dates from
-- other places with fall-through logic that prefers high quality dates but will make
-- do with low quality dates.

-- This SHOWS the actual contents of entity.collect_date that are wrong
-- 
-- In NEW SYSTEM the built in collect_date should not be homogenously
-- a single day, because that means its probably all the day that the
-- script was run, when it should be the visit_date at the worst or the
-- collect_date at the best. This is not the absolute best way to check
-- that the problem has been TRULY SOLVED but it is good enough for now
-- and the conceptuallly pure thing might be impossible without importing
-- a copy of the real world (because the real goal here is ultimately
-- just to make the data correspond to the world in a better way).
SELECT * FROM (
SELECT ARRAY(
         SELECT e.collect_date
           FROM entity e
           GROUP BY e.collect_date
       ) as collect_dates
  ) arr
  WHERE replace(split_part(array_dims(arr.collect_dates),':',1),'[','')::int = 1
;

-- This SHOWS probable errors in collect_date contents due to way too many
-- forms claiming to have been collected the same day.  This is another 
-- way to "gesture" towards the real problem that might be helpful.
SELECT collect_date, COUNT(*) AS total_forms
  FROM entity
  GROUP BY collect_date
  HAVING COUNT(*) > 800
;

-- This SHOWS the old datetimes associated with attribute-style collect_date's
SELECT sc.name AS schema_name
      ,a.name  AS attr_name
      ,COUNT(DISTINCT(v.value)) AS unique_collect_date_count
  FROM attribute a
    JOIN schema sc    ON sc.id = a.schema_id
    JOIN "datetime" v ON a.id = v.attribute_id
  WHERE a.name = 'date_collected'
  GROUP BY sc.name, a.name
;

-- This SHOWS the old collect_date attributes themselves
SELECT sc.name AS schema_name
      ,a.name  AS attr_name
  FROM attribute a
    JOIN schema sc    ON sc.id = a.schema_id
  WHERE a.name = 'date_collected'
;


