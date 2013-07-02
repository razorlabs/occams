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
  (select count(*) from value_decimal) as decimal_count,
  (select count(*) from value_integer) as integer_count,
  (select count(*) from value_datetime) as datetime_count,
  (select count(*) from value_string) as string_count,
  (select count(*) from value_choice) as choice_count,
  (select count(*) from value_text) as text_count,
  (select count(*) from value_blob) as blob_count
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



ROLLBACK;


