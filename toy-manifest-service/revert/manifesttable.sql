-- Revert flipr:manifesttable from pg

BEGIN;

DROP TABLE manifest_layers;

COMMIT;
