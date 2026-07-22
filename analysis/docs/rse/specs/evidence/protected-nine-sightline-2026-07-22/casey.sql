SELECT 'casey' AS sightline, CAST(169.983541700000 AS FLOAT) AS center_ra_deg, CAST(70.676222220000 AS FLOAT) AS center_dec_deg, r.*
INTO MyDB.f26_ps1strm_casey_20260722t172102z
FROM catalogRecordRowStore AS r
WHERE r.raMean >= 169.227181225290
  AND r.raMean <= 170.739902174709
  AND r.decMean >= 70.425944442222
  AND r.decMean <= 70.926499997778;
