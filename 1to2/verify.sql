BEGIN;

SELECT DISTINCT
  attribute.id
  , attribute.schema_id
  , schema.name
  , attribute.name
  , attribute."order"
FROM
  schema, attribute, section
WHERE
  schema.id = attribute.schema_id
  AND section.schema_id = attribute.schema_id
  AND attribute.section_id IS NULL
  AND attribute.type != 'object'
ORDER BY
  schema.name
  ;


-- Number of top-level schema with a mix of both object/scalar
SELECT COUNT(*)
FROM schema
WHERE NOT is_inline
AND EXISTS(SELECT 1 FROM attribute where schema.id = attribute.schema_id AND attribute.type = 'object')
AND EXISTS(SELECT 1 FROM attribute where schema.id = attribute.schema_id AND attribute.type != 'object')
;

-- Number of top-level schema with only scalar
SELECT COUNT(*)
FROM schema
WHERE NOT is_inline
AND NOT EXISTS(SELECT 1 FROM attribute where schema.id = attribute.schema_id AND attribute.type = 'object')
AND EXISTS(SELECT 1 FROM attribute where schema.id = attribute.schema_id AND attribute.type != 'object')
;

-- Number of top-level schema with only objects
SELECT COUNT(*)
FROM schema
WHERE NOT is_inline
AND EXISTS(SELECT 1 FROM attribute where schema.id = attribute.schema_id AND attribute.type = 'object')
AND NOT EXISTS(SELECT 2 FROM attribute where schema.id = attribute.schema_id AND attribute.type != 'object')
;

select
  section.id AS section_id
  ,schema_id
  ,schema.name AS schema_name
  ,section.name AS section_name
  ,"order"
from
  section
  ,schema
where
  section.schema_id = schema.id
  AND "order" = 0
  AND EXISTS(SELECT 1 FROM attribute where schema.id = attribute.schema_id AND attribute.type = 'object' AND section_id IS NULL)
  AND EXISTS(SELECT 1 FROM attribute where schema.id = attribute.schema_id AND attribute.type != 'object' AND section_id IS NULL)
order by
  schema_id
  ,"order"
;


WITH wtf AS (
  SELECT
    schema.id AS schema_id
    ,substring(schema.name for 32) AS schema_name
    ,section.name AS section_name
    ,section."order" AS section_order
    ,attribute.name AS attribute_name
    ,attribute."type"
    ,attribute."order" AS attribute_order
  FROM
    attribute
  JOIN schema
    ON schema.id = attribute.schema_id
  JOIN section
    ON section.id = attribute.section_id
    AND section.schema_id = schema.id
  ORDER BY
    substring(schema.name for 32)
    ,schema.id
    ,section."order"
    ,attribute."order"
)
SELECT * FROM wtf
;



select
  attribute.id as attribute_id
  , attribute.schema_id
  , schema.name as schema_id
  , attribute.name as attribute_name
  , attribute."type"
  , attribute."order"
from attribute
join schema on schema.id = attribute.schema_id
join attribute as parent on parent.object_schema_id = attribute.schema_id
where attribute.section_id is null
and attribute."type" != 'object';

\c postgres
drop database if exists _choice; create database _choice template _choice_009 owner plone;
\c _choice
select
  (select count(*) from value_decimal) as decimal
  ,(select count(*) from value_integer) as integer
  ,(select count(*) from value_datetime) as datetime
  ,(select count(*) from value_string) as string
  ,(select count(*) from value_choice) as choice
  ,(select count(*) from value_text) as text
  ,(select count(*) from value_blob) as blob
;

-- Delete sub-schemata
ROLLBACK;BEGIN;
DELETE
FROM schema
USING attribute
WHERE schema.id = attribute.object_schema_id
RETURNING schema.id
;
ROLLBACK;

-- Find orphaned child objects
-- (RESULT: turns out they are indeed orphaned, so we'll just purge them)
--WTF happend on 2012-06-16!!?
-- 2012-06-16
-- 2012-12-06
-- 2013-03-22
WITH wtf as (
SELECT
  value.id
  ,value.entity_id
  ,schema.id AS schema_id
  ,schema.name AS schema_name
  ,attribute.id AS attribute_id
  ,attribute.name AS attribute_name
  ,value.create_date
FROM "value_choice" AS value
JOIN attribute on attribute.id = value.attribute_id
JOIN schema on schema.id = attribute.schema_id
JOIN entity on entity.id = value.entity_id
WHERE
  (is_inline OR EXISTS(SELECT 1 FROM attribute AS parent where parent.object_schema_id = schema.id))
  AND NOT EXISTS (SELECT 1 FROM object where object.value = value.entity_id)
  )
select distinct cast(create_date as date) from wtf
;



ROLLBACK;


