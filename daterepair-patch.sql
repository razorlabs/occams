-- ----------------------
-- We need to patch the date_collected situation once we have forms and context for them.
-- The OTHER collection of SQL detects issues before, and verifies fixes after.
-- THIS SQL should be run in the middle to do the fixing!!
-- 
-- Run this, thusly:
-- /usr/bin/psql -h gibbon-test-db -d avrc_data -U plone -f daterepair-patch.sql

-- WARNING: This script is *actively dangerous* to run more than once.  If you run it
-- once, you'll update the collect_date's with the best possible data, which will be
-- erased afterwards.  If you run it a second time, you'll update the collect_date's
-- a SECOND TIME, without the benefit of the recently erased data, thus degrading the
-- data quality.  Care is required!  If this has been run "wrong" them you would
-- see colelct_date values that always perfect match the create_date or the visit_date
-- when that's available.  There would be ZERO exceptions from this trend, indicating
-- that the "valuably informative exceptions" have been purged by accident.  This state
-- of affairs, however, is *the best we can do* for certain forms that never had the
-- attribute "date_collected" in the first place.  Yes, its complicated.  Sorry.  The
-- best policy is simply to be careful.

-- ----------------------
-- We are transitioning from a regime where entity.collect_date is built into all forms
-- and date_collected attribute (which exists for some but not all forms) is being 
-- phased out.  Also, there is a "semi-bug" (makes sense for most things but not this?)
-- in datastore that leaves entity.collect_date as the **import** time rather than
-- something sane.  We're fixing this by adjusting entity.collect_date using dates from
-- other places with fall-through logic that prefers high quality dates but will make
-- do with low quality dates.

-- This FIXES the actual contents of entity.collect_date
UPDATE entity
  SET collect_date = (
         COALESCE(
          (SELECT DATE(v.value) -- attr_date_collected
             FROM "datetime" v
               JOIN attribute a ON a.id = v.attribute_id
             WHERE a.name = 'date_collected'
               AND entity.id = v.entity_id
          ) 
         ,(SELECT DATE(v.visit_date) -- visit_date_collected
             FROM visit v
               JOIN context c ON (v.id = c.key AND c.external = 'visit')
             WHERE entity.id = c.entity_id
          )
         ,DATE(entity.create_date))
         )
  FROM schema sc 
  WHERE sc.id = entity.schema_id
    AND sc.is_inline = false
;

-- This FIX deletes the old datetimes associated with attribute-style collect_date's
DELETE 
  FROM "datetime"
    USING attribute 
  WHERE attribute_id = attribute.id 
    AND attribute.name = 'date_collected'
;

-- This FIX deletes the old collect_date attributes themselves "as if they had never been"
DELETE
  FROM attribute 
  WHERE name = 'date_collected'
;

