/c avrc_data
BEGIN;
DELETE FROM entity WHERE id IN (
  SELECT
    entity.id
  FROM entity
  JOIN schema ON schema.id = entity.schema_id
  LEFT JOIN object on object.value = entity.id
  WHERE
    schema.is_inline
  AND
    object.id IS NULL
)
;
COMMIT;


SELECT
  entity.id
FROM entity
JOIN schema ON schema.id = entity.schema_id
LEFT JOIN object on object.value = entity.id
WHERE
  schema.is_inline
AND
  object.id IS NULL
  ;

