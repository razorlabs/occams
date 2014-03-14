---
--- Trigger initialization
---

CREATE EXTENSION postgres_fdw;

CREATE SERVER trigger_target FOREIGN DATA WRAPPER postgres_fdw OPTIONS (dbname 'trigger_target', port '9300');

CREATE USER MAPPING FOR USER SERVER trigger_target;
