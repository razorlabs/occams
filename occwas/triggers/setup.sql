---
--- Trigger initialization
---

CREATE EXTENSION postgres_fdw;

CREATE SERVER trigger_target FOREIGN DATA WRAPPER postgres_fdw OPTIONS (dbname 'trigger_target');

CREATE USER MAPPING FOR USER SERVER trigger_target;

---
--- Some tables define a ext_TABLE_id functions so that tables that have references
--- can properly find the referenced table in the remote system.
--- These functions cannot be used in the actual update triggers because the
--- data will have already changed by the time the function is useful.

--- Uses old_db/old_id semantics to reconcile both databases. In cases where the data exists in both
-- databases (such as user/patient/context), data is aligned by their unique key

--- Merge scenarios:
---   * Data exists in both databases and, thus, can have mismatching primary keys (user, all clinical, partner)
---       * Use unique keys (i.e, name, or zid)
---   * Data is poluated in both databases, but mutually exclusive (datastore phi/fia)
---       *  Use old_db/old_id
---   * Data is populated in only one database (calllog, lab)
---       * Use old_db/old_id



