SELECT 'chromatica' AS sightline, CAST(312.619125000000 AS FLOAT) AS center_ra_deg, CAST(73.900000000000 AS FLOAT) AS center_dec_deg, r.*
INTO MyDB.f26_ps1strm_chromatica_20260722t172102z
FROM catalogRecordRowStore AS r
WHERE r.raMean >= 311.716585846152
  AND r.raMean <= 313.521664153848
  AND r.decMean >= 73.649722222222
  AND r.decMean <= 74.150277777778;
