SELECT 'johndoeII' AS sightline, CAST(335.974750000000 AS FLOAT) AS center_ra_deg, CAST(73.025905560000 AS FLOAT) AS center_dec_deg, r.*
INTO MyDB.f26_ps1strm_johndoeII_20260722t172102z
FROM catalogRecordRowStore AS r
WHERE r.raMean >= 335.117426827991
  AND r.raMean <= 336.832073172009
  AND r.decMean >= 72.775627782222
  AND r.decMean <= 73.276183337778;
