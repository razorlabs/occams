---
--- Trigger initialization
---

CREATE EXTENSION postgres_fdw;

CREATE SERVER trigger_target FOREIGN DATA WRAPPER postgres_fdw OPTIONS (dbname 'trigger_target', port '9300');

CREATE USER MAPPING FOR USER SERVER trigger_target;

---
--- Some tables define a ext_TABLE_id functions so that tables that have references
--- can properly find the referenced table in the remote system.
--- These functions cannot be used in the actual update triggers because the
--- data will have already changed by the time the function is useful.


--- XXX: Some tables are just hopeless (call log...) in that
--- there is absolutely no possible way to insert/update
--- in id-agnostic way, so we need to hard code the ids
--- hopefully it doesn't screw up the serials....
