SELECT 'zach' AS sightline, CAST(310.199525000000 AS FLOAT) AS center_ra_deg, CAST(72.882327222200 AS FLOAT) AS center_dec_deg, r.*
INTO MyDB.f26_ps1strm_zach_20260722t172102z
FROM catalogRecordRowStore AS r
WHERE r.raMean >= 309.349180784603
  AND r.raMean <= 311.049869215397
  AND r.decMean >= 72.632049444422
  AND r.decMean <= 73.132604999978;
