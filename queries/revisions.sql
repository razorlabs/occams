-- From each form , get its:
--   * name
--   * current revision
--   * # revisions

SELECT  "schema_name",
        COUNT(DISTINCT "attribute_name") AS "num_fields",
        COUNT(*) - 1 AS "num_revisions",
        MIN("version_date") AS "create_date",
        MAX("version_date") AS "current_date"
FROM (
    
    -- Get all the revisions for a schema

	SELECT     "name" AS "schema_name",
	           NULL AS "attribute_name",
	           "create_date" AS "version_date"
	FROM       "schema"
	
	UNION
	
    SELECT     "name",
               NULL,
	           "remove_date"
	FROM       "schema"
	
	UNION
	
	-- Now for attributes
	
	SELECT     "schema"."name",
	           -- don't count object attributes (only the subobject attributes)
	           (
	               CASE WHEN "attribute"."type" != 'object'
	               THEN "schema"."name" || '.' || "attribute"."name"  
	               ELSE NULL
	               END
	           ),
	           "attribute"."create_date"
	FROM       "schema"
	JOIN       "attribute"
	ON         "schema"."id" = "attribute"."schema_id"
	    
	UNION       
	
	SELECT     "schema"."name",
	           NULL,
	           "attribute"."remove_date"
	FROM       "schema"
	JOIN       "attribute"
	ON         "schema"."id" = "attribute"."schema_id"
	
	-- Now for subform schema

	UNION
	
	SELECT     "schema"."name",
               NULL,
	           "subschema"."create_date"
	FROM       "schema"
	JOIN       "attribute"
	ON         "schema"."id" = "attribute"."schema_id"
	JOIN       "schema" AS "subschema"
	ON         "subschema"."id" = "attribute"."object_schema_id"
	
	UNION
	
    SELECT     "schema"."name",
               NULL,
               "subschema"."remove_date"
    FROM       "schema"
    JOIN       "attribute"
    ON         "schema"."id" = "attribute"."schema_id"
    JOIN       "schema" AS "subschema"
    ON         "subschema"."id" = "attribute"."object_schema_id"
	
    -- Now for attributes of subform schema
    
    UNION
    
    SELECT     "schema"."name",
               "subschema"."name" || '.' || "subattribute"."name",
               "subattribute"."create_date"
    FROM       "schema"
    JOIN       "attribute"
    ON         "schema"."id" = "attribute"."schema_id"
    JOIN       "schema" AS "subschema"
    ON         "subschema"."id" = "attribute"."object_schema_id"
    JOIN       "attribute" AS "subattribute"
    ON         "subattribute"."schema_id" = "subschema"."id"
    
    UNION
    
    SELECT     "schema"."name",
               NULL,
               "subattribute"."remove_date"
    FROM       "schema"
    JOIN       "attribute"
    ON         "schema"."id" = "attribute"."schema_id"
    JOIN       "schema" AS "subschema"
    ON         "subschema"."id" = "attribute"."object_schema_id"
    JOIN       "attribute" AS "subattribute"
    ON         "subattribute"."schema_id" = "subschema"."id"
    
	) AS "summary"
	
WHERE   TRUE 
AND     "version_date" IS NOT NULL
AND     "schema_name" NOT IN (
    SELECT "base"."name"
    FROM   "schema"
    JOIN   "schema" AS "base"
    ON     "schema"."base_schema_id" = "base"."id"
    GROUP BY "base"."name"
    )
AND     "schema_name" NOT IN (
    SELECT "schema"."name"
    FROM   "entity"
    JOIN   "object"
    ON     "object"."value" = "entity"."id"
    JOIN   "schema"
    ON     "schema"."id" = "entity"."schema_id"
    GROUP BY "schema"."name"
    )
GROUP BY "schema_name"
ORDER BY "schema_name"
;
