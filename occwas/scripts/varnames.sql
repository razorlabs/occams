BEGIN;

--- MHEALTH
UPDATE ONLY attribute SET name = 'creatinine_ccg' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'creatinine_cockcroftgalt' AND attribute.name = 'ChemistriesCreatinine';
UPDATE ONLY attribute SET name = 'sample0_actualtime' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'zero_sample_actualtime' AND attribute.name = 'PkSubStudySample1';
UPDATE ONLY attribute SET name = 'sample0_rifconc' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'zero_sample_rifampinconc' AND attribute.name = 'PkSubStudySample1';
UPDATE ONLY attribute SET name = 'sample0_schedtime' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'zero_sample_schedtime' AND attribute.name = 'PkSubStudySample1';
UPDATE ONLY attribute SET name = 'sample1_actualtime' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'one_sample_actualtime' AND attribute.name = 'PkSubStudySample2';
UPDATE ONLY attribute SET name = 'sample1_rifconc' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'one_sample_rifampinconc' AND attribute.name = 'PkSubStudySample2';
UPDATE ONLY attribute SET name = 'sample2_actualtime' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'two_sample_actualtime' AND attribute.name = 'PkSubStudySample3';
UPDATE ONLY attribute SET name = 'sample2_rifconc' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'two_sample_rifampinconc' AND attribute.name = 'PkSubStudySample3';
UPDATE ONLY attribute SET name = 'sample3_actualtime' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'three_sample_actualtime' AND attribute.name = 'PkSubStudySample4';
UPDATE ONLY attribute SET name = 'sample3_rifconc' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'three_sample_rifampinconc' AND attribute.name = 'PkSubStudySample4';
UPDATE ONLY attribute SET name = 'sample3_schedtime' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'three_sample_schedtime' AND attribute.name = 'PkSubStudySample4';
UPDATE ONLY attribute SET name = 'sample4_actualtime' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'four_sample_actualtime' AND attribute.name = 'PkSubStudySample5';
UPDATE ONLY attribute SET name = 'sample4_rifconc' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'four_sample_rifampinconc' AND attribute.name = 'PkSubStudySample5';
UPDATE ONLY attribute SET name = 'sample4_schedtime' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'four_sample_schedtime' AND attribute.name = 'PkSubStudySample5';
UPDATE ONLY attribute SET name = 'sample6_actualtime' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'six_sample_actualtime' AND attribute.name = 'PkSubStudySample6';
UPDATE ONLY attribute SET name = 'sample6_rifconc' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'six_sample_rifampinconc' AND attribute.name = 'PkSubStudySample6';
UPDATE ONLY attribute SET name = 'sample8_actualtime' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'eight_sample_actualtime' AND attribute.name = 'PkSubStudySample7';
UPDATE ONLY attribute SET name = 'sample8_rifconc' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'eight_sample_rifampinconc' AND attribute.name = 'PkSubStudySample7';
UPDATE ONLY attribute SET name = 'sample8_schedtime' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'eight_sample_schedtime' AND attribute.name = 'PkSubStudySample7';
UPDATE ONLY attribute SET name = 'sample24_actualtime' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'twentyfour_sample_actualtime' AND attribute.name = 'PkSubStudySample8';
UPDATE ONLY attribute SET name = 'sample24_inhconc' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'twentyfour_sample_inhconc' AND attribute.name = 'PkSubStudySample8';
UPDATE ONLY attribute SET name = 'sample24_rifconc' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'twentyfour_sample_rifampinconc' AND attribute.name = 'PkSubStudySample8';
UPDATE ONLY attribute SET name = 'sample24_schedtime' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'twentyfour_sample_schedtime' AND attribute.name = 'PkSubStudySample8';
UPDATE ONLY attribute SET name = 'sample24_sent' FROM schema  WHERE schema.id = attribute.schema_id AND schema.name = 'twentyfour_sample_sent' AND attribute.name = 'PkSubStudySample8';

ALTER TABLE attribute ALTER name TYPE VARCHAR(20);

