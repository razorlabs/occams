

-- In the NEW SYSTEM entities are unique over name/create_date
SELECT e.name, e.create_date, COUNT(*)
  FROM entity e
    -- JOIN datetime vd ON e.id = vd.entity_id
    -- JOIN schema sc ON sc.id = e.schema_id
  GROUP BY e.name, e.create_date
  HAVING COUNT(*) > 1
;

-- In ALL SYSTEMS, the the entity and attribute of every value should have the same schema_id
SELECT e.name, e.schema_id AS entity_schema_id ,sc_e.name AS entity_schema_name
       ,a.name ,a.schema_id AS attr_schema_id ,sc_a.name AS attr_schema_name
       ,v.*
  FROM entity e
    JOIN (
      SELECT to_char(value,'YYYY-MM-DD HH24:MI:SS'), id, 'datetime' AS table_type, entity_id, attribute_id FROM datetime
      UNION ALL
      SELECT to_char(value,'FM99999999999999'), id, 'integer' AS table_type, entity_id, attribute_id FROM integer
      UNION ALL
      SELECT to_char(value,'FM99999999999999.099999999'), id, 'decimal' AS table_type, entity_id, attribute_id FROM decimal
      UNION ALL
      SELECT value, id, 'string' AS table_type, entity_id, attribute_id FROM string
      UNION ALL
      SELECT to_char(value,'FM99999999999999'), id, 'object' AS table_type, entity_id, attribute_id FROM object
         ) v         ON e.id = v.entity_id
    JOIN attribute a ON a.id = v.attribute_id
    LEFT JOIN schema sc_e ON sc_e.id = e.schema_id
    LEFT JOIN schema sc_a ON sc_a.id = a.schema_id
  WHERE e.schema_id != a.schema_id
;


-- In ALL SYSTEMS the form names match associated schema names
SELECT e.id
      ,e.name AS entity_name
      ,e.create_date AS entity_date
      ,e.revision
      ,sc.name AS schema_name
      ,sc.create_date AS schema_date
  FROM entity e
    JOIN schema sc ON sc.id = e.schema_id
  WHERE sc.name NOT LIKE '%'||substring(e.name from 1 for position('-' in e.name)-1)||'%'
;

-- In ALL SYSTEMS the is_collection attributes have associated choices
SELECT a.name, ch.*
  FROM attribute a 
    LEFT JOIN choice ch on a.id = ch.attribute_id
  WHERE a.is_collection
    AND ch.id IS NULL
;

-- In ALL SYSTEMS every schema should have at least one attribute
SELECT sc.name, sc.publish_date, att.*
  FROM schema sc
    LEFT JOIN attribute att ON sc.id = att.schema_id
  WHERE att.id IS NULL
  ORDER BY sc.name, sc.publish_date, att.order
;


-- In the NEW SYSTEM, when revisioning happens, COUNT(audit)+1 
-- should equal entity.revision
SELECT e.name, e.revision, COUNT(*)
  FROM entity_audit a
    RIGHT JOIN entity e ON a.id = e.id
  WHERE e.revision > 1
  GROUP BY e.name, e.revision
  HAVING COUNT(*)+1 != e.revision
;

-- In the NEW SYSTEM, when revisioning happens, the summation n(n-1)/2
-- over the audit table should predict the current revision number.
SELECT e.name, e.revision, COUNT(*), SUM(a.revision)
  FROM entity_audit a
    RIGHT JOIN entity e ON a.id = e.id
  GROUP BY e.name, e.revision
  HAVING SUM(a.revision) != (e.revision * (e.revision - 1)) / 2
;


-- In the NEW SYSTEM, when revisioning happens, the summation n(n-1)/2
-- over the audit table should predict the current revision number for
-- all of the value tables (datetime, string, etc).
SELECT v.id, v.revision, COUNT(*), SUM(a.revision), 'datetime' as src_table
  FROM datetime_audit a
    RIGHT JOIN datetime v ON v.id = a.id
  GROUP BY v.id, v.revision
  HAVING SUM(a.revision) != (v.revision * (v.revision - 1)) / 2
UNION ALL
SELECT v.id, v.revision, COUNT(*), SUM(a.revision), 'datetime' as src_table
  FROM string_audit a
    RIGHT JOIN string v ON v.id = a.id
  GROUP BY v.id, v.revision
  HAVING SUM(a.revision) != (v.revision * (v.revision - 1)) / 2
UNION ALL
SELECT v.id, v.revision, COUNT(*), SUM(a.revision), 'datetime' as src_table
  FROM integer_audit a
    RIGHT JOIN integer v ON v.id = a.id
  GROUP BY v.id, v.revision
  HAVING SUM(a.revision) != (v.revision * (v.revision - 1)) / 2
UNION ALL
SELECT v.id, v.revision, COUNT(*), SUM(a.revision), 'datetime' as src_table
  FROM decimal_audit a
    RIGHT JOIN decimal v ON v.id = a.id
  GROUP BY v.id, v.revision
  HAVING SUM(a.revision) != (v.revision * (v.revision - 1)) / 2
;


-- In ALL SYSTEMS, we expect attr.create_date >= schema.create_date
SELECT *
  FROM schema sc
    LEFT JOIN attribute a ON sc.id = a.schema_id
  WHERE a.create_date < sc.create_date
;

-- In ALL SYSTEMS, we expect attr.create_date >= schema.create_date
SELECT *
  FROM schema sc
    LEFT JOIN attribute a ON sc.id = a.schema_id
  WHERE a.create_date < sc.create_date
;

-- In ALL SYSTEMS, we expect value.create_date >= entity.create_date
SELECT *
  FROM entity e
    JOIN (
      SELECT to_char(value,'YYYY-MM-DD HH24:MI:SS') AS value, id, 'datetime' AS table_type, entity_id ,attribute_id , create_date FROM datetime
      UNION ALL
      SELECT to_char(value,'FM99999999999999'), id, 'integer' AS table_type, entity_id ,attribute_id , create_date FROM integer
      UNION ALL
      SELECT to_char(value,'FM99999999999999.099999999'), id, 'decimal' AS table_type, entity_id ,attribute_id , create_date FROM decimal
      UNION ALL
      SELECT value, id, 'string' AS table_type, entity_id ,attribute_id , create_date FROM string
      UNION ALL
      SELECT to_char(value,'FM99999999999999'), id, 'object' AS table_type, entity_id ,attribute_id ,create_date FROM object
         ) v         ON e.id = v.entity_id
    RIGHT JOIN entity e2 ON (table_type = 'object' AND CAST(v.value AS integer) = e.id)
  WHERE v.create_date < COALESCE(e.create_date, e2.create_date)
;


-- In ALL SYSTEMS, we expect entity.create_date >= schema.create_date
SELECT e.name AS entity_name
      ,e.create_date AS entity_create
      ,e.modify_date AS entity_modify
      ,sc.create_date AS schema_create
      ,sc.name AS schema_name, sc.*
  FROM schema sc
    LEFT JOIN entity e ON sc.id = e.schema_id
  WHERE e.create_date < sc.create_date 
;


-- Child schemas should have is_inline = true so they can be easily detected
-- and managed.  This will show too few or too many is_inline values:
SELECT sc.name
      ,a.name
      ,(a.name IS NULL AND sc.is_inline = True) AS spurious
      ,(a.name IS NOT NULL AND sc.is_inline = False) AS missing
  FROM schema sc
    LEFT JOIN attribute a ON (sc.id = a.object_schema_id)
  WHERE (a.name IS NULL AND sc.is_inline = True)
     OR (a.name IS NOT NULL AND sc.is_inline = False)
;

-- In NEW SYSTEM, we expect no extraneous values when attribute.is_collection = false
-- (This QA constraint was added when it was understood that something in the new
-- versioning import was breaking the assumption.)
SELECT v.entity_id, a.name, COUNT(*)
  FROM (
      SELECT to_char(value,'YYYY-MM-DD HH24:MI:SS'), id, 'datetime' AS table_type, entity_id, attribute_id FROM datetime
      UNION ALL
      SELECT to_char(value,'FM99999999999999'), id, 'integer' AS table_type, entity_id, attribute_id FROM integer
      UNION ALL
      SELECT to_char(value,'FM99999999999999.099999999'), id, 'decimal' AS table_type, entity_id, attribute_id FROM decimal
      UNION ALL
      SELECT value, id, 'string' AS table_type, entity_id, attribute_id FROM string
      UNION ALL
      SELECT to_char(value,'FM99999999999999'), id, 'object' AS table_type, entity_id, attribute_id FROM object
         ) v
    JOIN attribute a ON a.id = v.attribute_id
    -- LEFT JOIN schema sc_e ON sc_e.id = e.schema_id
    -- LEFT JOIN schema sc_a ON sc_a.id = a.schema_id
  WHERE a.is_collection = false
  GROUP BY v.entity_id, a.name
  HAVING COUNT(*) > 1
;

-- In NEW SYSTEM, we expect all string values to line up
-- with a choice value.  (Note that some "boolean" int
-- values will line up with choice.value text of "True"
-- and "False" which is weird, and which this *properly*
-- ignores for the sake of QA work.)
SELECT c_actual.attribute_id
      ,c_actual.choice_id
      ,c_actual.value
      ,c_expect.attribute_id
      ,c_expect.value
  FROM (
    SELECT st.value, st.attribute_id, st.choice_id
      FROM string st
      WHERE choice_id IS NOT NULL
      GROUP BY st.value, st.attribute_id, st.choice_id
       ) c_actual
    LEFT JOIN (
    SELECT ch.value, ch.attribute_id
      FROM choice ch
       ) c_expect 
    ON (c_actual.attribute_id = c_expect.attribute_id
    AND c_actual.value        = c_expect.value)
  WHERE c_actual.value IS NULL
  ORDER BY c_actual.attribute_id, c_actual.value
;

-- In the NEW SYSTEM, we expect that every patient_id stored in
-- the context table as a "patient" key, should match an entry
-- in the patient (formerly subject) table.
SELECT *
  FROM context pc
    LEFT JOIN patient p ON (pc.key = p.id)
  WHERE pc.external = 'patient'
    AND p.our IS NULL
  LIMIT 10
;

-- In NEW SYSTEM the built in collect_date should not be homogenously
-- a single day, because that means its probably all the day that the
-- script was run, when it should be the visit_date at the worst or the
-- collect_date at the best.
SELECT * FROM (
SELECT ARRAY(
         SELECT e.collect_date
           FROM entity e
           GROUP BY e.collect_date
       ) as collect_dates
  ) arr
  WHERE replace(split_part(array_dims(arr.collect_dates),':',1),'[','')::int = 1
;


-- In BOTH SYSTEMS if a schema has entities and attributes, then every
-- string attribute should have at least one value in the string table.
-- (Other than a few rare/wierd things that can be excepted below...)
SELECT grp.schema_name, grp.attr_name, COUNT(*), MIN(grp.value), MAX(grp.value)
  FROM (
    SELECT sc.name AS schema_name
          ,a.name  AS attr_name
          ,v.value
      FROM schema sc
        JOIN entity e      ON sc.id = e.schema_id
        JOIN attribute a   ON sc.id = a.schema_id
        LEFT JOIN string v ON (e.id = v.entity_id AND a.id = v.attribute_id)
      WHERE a.type = 'string'
        AND a.name NOT LIKE '%comment%' -- "GenitalSecretions","comments" is empty in source
        AND a.name NOT LIKE '%reason' -- "ScreeningRouteOfTransmission027","nonenrollment_reason"
      GROUP BY sc.name, a.name, v.value
       ) grp
  GROUP BY grp.schema_name, grp.attr_name
  HAVING COUNT(*) = 1
     AND MIN(grp.value) IS NULL
;


