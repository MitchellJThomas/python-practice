-- Deploy toy-manifest-service:partitions_0 to pg
-- requires: manifesttable

BEGIN;

CREATE TABLE manifest_layers_42_2020 PARTITION OF manifest_layers
    FOR VALUES FROM ('2020-10-15') TO ('2020-10-22');
CREATE INDEX manifest_layers_42_2020_manifest_config_digest_idx on manifest_layers_42_2020 (manifest_config_digest);
CREATE INDEX manifest_layers_42_2020_digest_idx on manifest_layers_42_2020 (digest);
    
CREATE TABLE manifest_layers_43_2020 PARTITION OF manifest_layers
    FOR VALUES FROM ('2020-10-22') TO ('2020-10-29');
CREATE INDEX manifest_layers_43_2020_manifest_config_digest_idx on manifest_layers_43_2020 (manifest_config_digest);
CREATE INDEX manifest_layers_43_2020_digest_idx on manifest_layers_43_2020 (digest);
    
CREATE TABLE manifest_layers_44_2020 PARTITION OF manifest_layers
    FOR VALUES FROM ('2020-10-29') TO ('2020-11-05');
CREATE INDEX manifest_layers_44_2020_manifest_config_digest_idx on manifest_layers_44_2020 (manifest_config_digest);
CREATE INDEX manifest_layers_44_2020_digest_idx on manifest_layers_44_2020 (digest);
    
CREATE TABLE manifest_layers_45_2020 PARTITION OF manifest_layers
    FOR VALUES FROM ('2020-11-05') TO ('2020-11-12');
CREATE INDEX manifest_layers_45_2020_manifest_config_digest_idx on manifest_layers_45_2020 (manifest_config_digest);
CREATE INDEX manifest_layers_45_2020_digest_idx on manifest_layers_45_2020 (digest);
    
CREATE TABLE manifest_layers_46_2020 PARTITION OF manifest_layers
    FOR VALUES FROM ('2020-11-12') TO ('2020-11-19');
CREATE INDEX manifest_layers_46_2020_manifest_config_digest_idx on manifest_layers_46_2020 (manifest_config_digest);
CREATE INDEX manifest_layers_46_2020_digest_idx on manifest_layers_46_2020 (digest);
    
CREATE TABLE manifest_layers_47_2020 PARTITION OF manifest_layers
    FOR VALUES FROM ('2020-11-19') TO ('2020-11-26');
CREATE INDEX manifest_layers_47_2020_manifest_config_digest_idx on manifest_layers_47_2020 (manifest_config_digest);
CREATE INDEX manifest_layers_47_2020_digest_idx on manifest_layers_47_2020 (digest);
    
CREATE TABLE manifest_layers_48_2020 PARTITION OF manifest_layers
    FOR VALUES FROM ('2020-11-26') TO ('2020-12-03');
CREATE INDEX manifest_layers_48_2020_manifest_config_digest_idx on manifest_layers_48_2020 (manifest_config_digest);
CREATE INDEX manifest_layers_48_2020_digest_idx on manifest_layers_48_2020 (digest);
    
CREATE TABLE manifest_layers_49_2020 PARTITION OF manifest_layers
    FOR VALUES FROM ('2020-12-03') TO ('2020-12-10');
CREATE INDEX manifest_layers_49_2020_manifest_config_digest_idx on manifest_layers_49_2020 (manifest_config_digest);
CREATE INDEX manifest_layers_49_2020_digest_idx on manifest_layers_49_2020 (digest);
    
CREATE TABLE manifest_layers_50_2020 PARTITION OF manifest_layers
    FOR VALUES FROM ('2020-12-10') TO ('2020-12-17');
CREATE INDEX manifest_layers_50_2020_manifest_config_digest_idx on manifest_layers_50_2020 (manifest_config_digest);
CREATE INDEX manifest_layers_50_2020_digest_idx on manifest_layers_50_2020 (digest);
    
CREATE TABLE manifest_layers_51_2020 PARTITION OF manifest_layers
    FOR VALUES FROM ('2020-12-17') TO ('2020-12-24');
CREATE INDEX manifest_layers_51_2020_manifest_config_digest_idx on manifest_layers_51_2020 (manifest_config_digest);
CREATE INDEX manifest_layers_51_2020_digest_idx on manifest_layers_51_2020 (digest);
    
CREATE TABLE manifest_layers_52_2020 PARTITION OF manifest_layers
    FOR VALUES FROM ('2020-12-24') TO ('2020-12-31');
CREATE INDEX manifest_layers_52_2020_manifest_config_digest_idx on manifest_layers_52_2020 (manifest_config_digest);
CREATE INDEX manifest_layers_52_2020_digest_idx on manifest_layers_52_2020 (digest);
    
CREATE TABLE manifest_layers_53_2020 PARTITION OF manifest_layers
    FOR VALUES FROM ('2020-12-31') TO ('2021-01-07');
CREATE INDEX manifest_layers_53_2020_manifest_config_digest_idx on manifest_layers_53_2020 (manifest_config_digest);
CREATE INDEX manifest_layers_53_2020_digest_idx on manifest_layers_53_2020 (digest);
    
CREATE INDEX manifest_config_digest_idx on manifest_layers (manifest_config_digest);
CREATE INDEX digest_idx on manifest_layers (digest);
    
COMMIT;
