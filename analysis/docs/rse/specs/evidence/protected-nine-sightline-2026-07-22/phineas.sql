SELECT 'phineas' AS sightline, CAST(177.781333333300 AS FLOAT) AS center_ra_deg, CAST(71.695638888900 AS FLOAT) AS center_dec_deg, r.*
INTO MyDB.f26_ps1strm_phineas_20260722t172102z
FROM catalogRecordRowStore AS r
WHERE r.raMean >= 176.984411441898
  AND r.raMean <= 178.578255224702
  AND r.decMean >= 71.445361111122
  AND r.decMean <= 71.945916666678;
