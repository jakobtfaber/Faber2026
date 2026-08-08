SELECT 'hamilton' AS sightline, CAST(305.037166666700 AS FLOAT) AS center_ra_deg, CAST(70.792766666700 AS FLOAT) AS center_dec_deg, r.*
INTO MyDB.f26_ps1strm_hamilton_20260722t172102z
FROM catalogRecordRowStore AS r
WHERE r.raMean >= 304.276391323244
  AND r.raMean <= 305.797942010156
  AND r.decMean >= 70.542488888922
  AND r.decMean <= 71.043044444478;
