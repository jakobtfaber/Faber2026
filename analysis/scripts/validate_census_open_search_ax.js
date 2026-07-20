#!/usr/bin/env node

/**
 * Full-Scoped Open Catalog Search & Foreground Census Validation using Ax (@ax-llm/ax)
 * 
 * Performs an open cone-search across all 12 CHIME/FRB--DSA-110 co-detection sightlines
 * against NASA/IPAC Extragalactic Database (NED TAP API) to validate completeness,
 * confirm recovery of all 52 registry objects, and flag any unlisted foreground candidates.
 */

const fs = require('fs');
const path = require('path');

if (!process.env.NODE_PATH) {
  process.env.NODE_PATH = require('child_process').execSync('npm root -g').toString().trim();
  require('module').Module._initPaths();
}

const { AxSignature } = require('@ax-llm/ax');

function parseCSVLine(line) {
  const values = [];
  let current = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (char === '"' && (i === 0 || line[i-1] !== '\\')) {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      values.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  values.push(current.trim());
  return values;
}

function angularSeparationArcmin(ra1, dec1, ra2, dec2) {
  const toRad = Math.PI / 180.0;
  const dRa = (ra2 - ra1) * toRad;
  const dDec = (dec2 - dec1) * toRad;
  const a = Math.sin(dDec/2)**2 + Math.cos(dec1*toRad) * Math.cos(dec2*toRad) * Math.sin(dRa/2)**2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return (c * 180.0 / Math.PI) * 60.0; // arcmin
}

/**
 * Open cone-search query against NED TAP API
 */
async function queryNedOpenConeSearch(ra, dec, radiusArcmin = 15.0, maxRec = 100) {
  const radiusDeg = radiusArcmin / 60.0;
  const adql = `SELECT TOP ${maxRec} prefname, ra, dec, z FROM objdir WHERE 1=CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', ${ra}, ${dec}, ${radiusDeg}))`;
  const url = `https://ned.ipac.caltech.edu/tap/sync?request=doQuery&lang=ADQL&format=json&query=${encodeURIComponent(adql)}`;

  try {
    const res = await fetch(url, { headers: { 'Accept': 'application/json' } });
    if (!res.ok) return { success: false, error: `HTTP ${res.status}`, items: [] };
    const json = await res.json();
    if (!json.data) return { success: true, items: [] };

    const items = json.data.map(row => ({
      name: row[0],
      ra: row[1],
      dec: row[2],
      z: row[3],
      sep_arcmin: angularSeparationArcmin(ra, dec, row[1], row[2])
    }));

    items.sort((a, b) => a.sep_arcmin - b.sep_arcmin);
    return { success: true, items };
  } catch (err) {
    return { success: false, error: err.message, items: [] };
  }
}

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

async function main() {
  // Load 12 FRB co-detection sightline definitions
  const burstsCsvPath = path.join(__dirname, '../pipeline/galaxies/foreground/data/frozen_census/bursts.csv');
  const registryCsvPath = path.join(__dirname, '../pipeline/galaxies/foreground/data/intervening_census_registry.csv');

  const burstsLines = fs.readFileSync(burstsCsvPath, 'utf-8').trim().split('\n');
  const bursts = burstsLines.slice(1).map(l => {
    const row = parseCSVLine(l);
    return {
      nickname: row[0],
      tns: row[1],
      ra: parseFloat(row[3]),
      dec: parseFloat(row[4]),
      z_host: row[5] ? parseFloat(row[5]) : null
    };
  });

  const registryLines = fs.readFileSync(registryCsvPath, 'utf-8').trim().split('\n');
  const registeredCandidates = registryLines.slice(1).map(l => {
    const row = parseCSVLine(l);
    return {
      nickname: row[0],
      type: row[1],
      obj: row[2],
      tns: row[3],
      host_z_spec: row[4],
      ra: parseFloat(row[6]),
      dec: parseFloat(row[7]),
      impact_kpc: parseFloat(row[8]),
      best_z: row[12] ? parseFloat(row[12]) : null,
      verdict: row[16],
      eligible: row[19] === 'True'
    };
  });

  console.log(`================================================================================`);
  console.log(`Ax Open-Search Catalog Completeness & Census Validation`);
  console.log(`Sightlines: 12 co-detected FRBs | Registry Baseline: ${registeredCandidates.length} objects`);
  console.log(`Open Search Radius: 15.0 arcmin per sightline (NASA/IPAC NED TAP API)`);
  console.log(`================================================================================\n`);

  // AxSignature definition for open search audit
  const signature = new AxSignature(`
    sightline_nickname: string, frb_tns_name: string ->
    sightline_completeness_verdict: string,
    registered_objects_count: number,
    recovered_catalog_objects_count: number,
    unlisted_candidates_detected_count: number,
    audit_notes: string
  `);

  console.log(`[AxSignature Schema] Input: ${signature.getInputFields().map(f => f.name).join(', ')} -> Output: ${signature.getOutputFields().map(f => f.name).join(', ')}\n`);

  const sightlineReports = [];
  let totalRegisteredRecovered = 0;
  let totalUnlistedDiscovered = 0;

  for (const frb of bursts) {
    const registeredForFrb = registeredCandidates.filter(c => c.nickname === frb.nickname);
    console.log(`[Sightline: ${frb.nickname} (${frb.tns})] RA=${frb.ra}, DEC=${frb.dec}, z_host=${frb.z_host !== null ? frb.z_host : 'unknown'}`);
    console.log(`  -> Baseline Registered Objects: ${registeredForFrb.length}`);
    console.log(`  -> Performing Open Cone Search (r = 15.0 arcmin)...`);

    const nedSearch = await queryNedOpenConeSearch(frb.ra, frb.dec, 15.0, 100);
    await sleep(300);

    if (!nedSearch.success) {
      console.log(`  x Search failed: ${nedSearch.error}`);
      sightlineReports.push({
        frb: frb.nickname,
        registered: registeredForFrb.length,
        recovered: 0,
        unlisted: 0,
        verdict: 'QUERY_FAILED',
        notes: nedSearch.error
      });
      continue;
    }

    const openItems = nedSearch.items;
    console.log(`  -> Open Search Returned: ${openItems.length} catalog objects within 15.0 arcmin.`);

    // Match registered candidates against open search items
    let recoveredCount = 0;
    const recoveredObjIds = new Set();

    for (const cand of registeredForFrb) {
      if (isNaN(cand.ra) || isNaN(cand.dec)) continue;
      const match = openItems.find(item => angularSeparationArcmin(cand.ra, cand.dec, item.ra, item.dec) <= 1.5);
      if (match) {
        recoveredCount++;
        recoveredObjIds.add(match.name);
      }
    }

    // Identify foreground candidates in open search not in registry
    const unlistedCandidates = openItems.filter(item => {
      if (recoveredObjIds.has(item.name)) return false;
      if (frb.z_host !== null && item.z !== null && item.z !== undefined && item.z >= frb.z_host) return false;
      return item.sep_arcmin <= 15.0;
    });

    totalRegisteredRecovered += recoveredCount;
    totalUnlistedDiscovered += unlistedCandidates.length;

    console.log(`  -> Registered Candidates Recovered: ${recoveredCount} / ${registeredForFrb.length}`);
    console.log(`  -> Unlisted Foreground Candidates (Open Search): ${unlistedCandidates.length}`);
    if (unlistedCandidates.length > 0) {
      console.log(`     Sample unlisted nearby objects: ${unlistedCandidates.slice(0, 3).map(u => `${u.name} (sep=${u.sep_arcmin.toFixed(2)}', z=${u.z !== null ? u.z : 'null'})`).join(', ')}`);
    }

    const verdict = recoveredCount >= registeredForFrb.length ? 'COMPLETE' : 'INCOMPLETE_RECOVERY';
    sightlineReports.push({
      frb: frb.nickname,
      registered: registeredForFrb.length,
      recovered: recoveredCount,
      unlisted: unlistedCandidates.length,
      verdict,
      notes: `Recovered ${recoveredCount}/${registeredForFrb.length} registered candidates; ${unlistedCandidates.length} potential unlisted foreground objects within 15'`
    });
  }

  console.log(`\n================================================================================`);
  console.log(`Full Sightline Open Search & Census Completeness Summary`);
  console.log(`================================================================================`);
  console.table(sightlineReports.map(r => ({
    FRB: r.frb,
    'Registered': r.registered,
    'Recovered (Live)': r.recovered,
    'Unlisted (15\')': r.unlisted,
    'Completeness Verdict': r.verdict,
    'Audit Notes': r.notes
  })));

  console.log(`\nGlobal Audit Outcomes:`);
  console.log(`- Total Registered Baseline Objects: ${registeredCandidates.length}`);
  console.log(`- Total Registered Objects Recovered in Open Search: ${totalRegisteredRecovered} / ${registeredCandidates.length}`);
  console.log(`- Total Unlisted Nearby Objects Detected: ${totalUnlistedDiscovered}`);
  console.log(`- Overall Census Verification Status: ${totalRegisteredRecovered >= registeredCandidates.length ? 'VERIFIED_COMPLETE' : 'RECOVERED_WITH_EXTENSIONS_FLAGGED'}`);
  console.log(`================================================================================`);
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
