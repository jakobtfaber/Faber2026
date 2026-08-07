SELECT 'isha' AS sightline, CAST(71.411000000000 AS FLOAT) AS center_ra_deg, CAST(70.307388888900 AS FLOAT) AS center_dec_deg, r.*
INTO MyDB.f26_ps1strm_isha_20260722t172102z
FROM catalogRecordRowStore AS r
WHERE r.raMean >= 70.668259883074
  AND r.raMean <= 72.153740116926
  AND r.decMean >= 70.057111111122
  AND r.decMean <= 70.557666666678;
