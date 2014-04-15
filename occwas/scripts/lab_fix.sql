-- Lab is just a cludge of bad design deisions, fix them here

ALTER TABLE site_lab_location ALTER location_id SET NOT NULL;
ALTER TABLE site_lab_location DROP CONSTRAINT site_lab_location_pkey;
ALTER TABLE site_lab_location ADD CONSTRAINT site_lab_location_pkey PRIMARY KEY (site_id, location_id);
