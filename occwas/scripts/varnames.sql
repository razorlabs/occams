BEGIN;

--- MHEALTH
UPDATE ONLY attribute SET name = 'creatinine_ccg' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'ChemistriesCreatinine' AND attribute.name = 'creatinine_cockcroftgalt';
UPDATE ONLY attribute SET name = 'sample0_actualtime' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'PkSubStudySample1' AND attribute.name = 'zero_sample_actualtime';
UPDATE ONLY attribute SET name = 'sample0_rifconc' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'PkSubStudySample1' AND attribute.name = 'zero_sample_rifampinconc';
UPDATE ONLY attribute SET name = 'sample0_schedtime' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'PkSubStudySample1' AND attribute.name = 'zero_sample_schedtime';
UPDATE ONLY attribute SET name = 'sample1_actualtime' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'PkSubStudySample2' AND attribute.name = 'one_sample_actualtime';
UPDATE ONLY attribute SET name = 'sample1_rifconc' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'PkSubStudySample2' AND attribute.name = 'one_sample_rifampinconc';
UPDATE ONLY attribute SET name = 'sample2_actualtime' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'PkSubStudySample3' AND attribute.name = 'two_sample_actualtime';
UPDATE ONLY attribute SET name = 'sample2_rifconc' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'PkSubStudySample3' AND attribute.name = 'two_sample_rifampinconc';
UPDATE ONLY attribute SET name = 'sample3_actualtime' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'PkSubStudySample4' AND attribute.name = 'three_sample_actualtime';
UPDATE ONLY attribute SET name = 'sample3_rifconc' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'PkSubStudySample4' AND attribute.name = 'three_sample_rifampinconc';
UPDATE ONLY attribute SET name = 'sample3_schedtime' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'PkSubStudySample4' AND attribute.name = 'three_sample_schedtime';
UPDATE ONLY attribute SET name = 'sample4_actualtime' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'PkSubStudySample5' AND attribute.name = 'four_sample_actualtime';
UPDATE ONLY attribute SET name = 'sample4_rifconc' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'PkSubStudySample5' AND attribute.name = 'four_sample_rifampinconc';
UPDATE ONLY attribute SET name = 'sample4_schedtime' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'PkSubStudySample5' AND attribute.name = 'four_sample_schedtime';
UPDATE ONLY attribute SET name = 'sample6_actualtime' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'PkSubStudySample6' AND attribute.name = 'six_sample_actualtime';
UPDATE ONLY attribute SET name = 'sample6_rifconc' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'PkSubStudySample6' AND attribute.name = 'six_sample_rifampinconc';
UPDATE ONLY attribute SET name = 'sample8_actualtime' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'PkSubStudySample7' AND attribute.name = 'eight_sample_actualtime';
UPDATE ONLY attribute SET name = 'sample8_rifconc' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'PkSubStudySample7' AND attribute.name = 'eight_sample_rifampinconc';
UPDATE ONLY attribute SET name = 'sample8_schedtime' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'PkSubStudySample7' AND attribute.name = 'eight_sample_schedtime';
UPDATE ONLY attribute SET name = 'sample24_actualtime' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'PkSubStudySample8' AND attribute.name = 'twentyfour_sample_actualtime';
UPDATE ONLY attribute SET name = 'sample24_inhconc' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'PkSubStudySample8' AND attribute.name = 'twentyfour_sample_inhconc';
UPDATE ONLY attribute SET name = 'sample24_rifconc' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'PkSubStudySample8' AND attribute.name = 'twentyfour_sample_rifampinconc';
UPDATE ONLY attribute SET name = 'sample24_schedtime' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'PkSubStudySample8' AND attribute.name = 'twentyfour_sample_schedtime';
UPDATE ONLY attribute SET name = 'sample24_sent' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'PkSubStudySample8' AND attribute.name = 'twentyfour_sample_sent';


ALTER TABLE attribute ALTER name TYPE VARCHAR(20);

