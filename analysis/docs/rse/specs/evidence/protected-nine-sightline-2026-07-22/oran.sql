SELECT 'oran' AS sightline, CAST(318.044833333300 AS FLOAT) AS center_ra_deg, CAST(72.827277777800 AS FLOAT) AS center_dec_deg, r.*
INTO MyDB.f26_ps1strm_oran_20260722t172102z
FROM catalogRecordRowStore AS r
WHERE r.raMean >= 317.197133477164
  AND r.raMean <= 318.892533189436
  AND r.decMean >= 72.577000000022
  AND r.decMean <= 73.077555555578;
