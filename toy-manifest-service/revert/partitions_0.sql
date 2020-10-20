-- Revert toy-manifest-service:partitions_0 from pg

BEGIN;

DROP INDEX manifest_lahyers_digest_idx;
DROP TABLE manifest_layers_42_2020;
DROP TABLE manifest_layers_43_2020;
DROP TABLE manifest_layers_44_2020;
DROP TABLE manifest_layers_45_2020;
DROP TABLE manifest_layers_46_2020;
DROP TABLE manifest_layers_47_2020;
DROP TABLE manifest_layers_48_2020;
DROP TABLE manifest_layers_49_2020;
DROP TABLE manifest_layers_50_2020;
DROP TABLE manifest_layers_51_2020;
DROP TABLE manifest_layers_52_2020;
DROP TABLE manifest_layers_53_2020;

COMMIT;
