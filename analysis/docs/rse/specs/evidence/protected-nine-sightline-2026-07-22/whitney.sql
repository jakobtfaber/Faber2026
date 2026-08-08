SELECT 'whitney' AS sightline, CAST(134.720500000000 AS FLOAT) AS center_ra_deg, CAST(73.490833333300 AS FLOAT) AS center_dec_deg, r.*
INTO MyDB.f26_ps1strm_whitney_20260722t172102z
FROM catalogRecordRowStore AS r
WHERE r.raMean >= 133.839731629318
  AND r.raMean <= 135.601268370682
  AND r.decMean >= 73.240555555522
  AND r.decMean <= 73.741111111078;
