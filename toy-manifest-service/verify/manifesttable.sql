-- Verify flipr:manifesttable on pg

SELECT
     annotations,
     digest,
     media_type,
     layer_order,
     layer_size,
     ts,
     urls,
     manifest_config_digest,
     manifest_config_media_type,
     manifest_config_size,
     manifest_media_type,
     manifest_schema_version
  FROM manifest_layers
WHERE FALSE;
