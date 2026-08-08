#!/usr/bin/env python
"""Cost ladder for the exploratory fast joint fit.

Measures end-to-end wall clock of the plain joint-fit driver as a function of
the dynamic-spectrum decimation AND the sampler settings, so the two can be
told apart. Everything else -- pulse-broadening family, priors, masks, inputs,
component counts -- is held at the campaign values.

This is exploration, not the frozen component-count contract. Nothing here is
admissible as component-count evidence.
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path.home() / "zach_fast_20260805"
ANALYSIS = Path.home() / "zach_count_20260731/src/analysis"
PY = ANALYSIS / ".venv/bin/python"
JOINT = ANALYSIS / "scattering/studies/joint-refits"
DSA = "/home/ubuntu/flits-runs/data/dsa/zach_dsa_I_262_368_2500b_cntr_bpc.npy"
CHIME = "/home/ubuntu/flits-runs/data/zach_chime_I_262_3621_32000b_cntr_bpc.npy"

BASE = {
    "chunk_size": 2000, "diagnostics": True, "extend_chain": True,
    "fitting_method": "nested", "max_chunks": 5, "model_scan": True, "nlive": 400,
    "nproc": 8, "onpulse_pad_factor": 0.5, "outer_trim": 0.15,
    "plot": True, "steps": 10000,
    "sampcfg_path": str(ANALYSIS / "radio_pipeline/resources/scattering_sampler.yaml"),
    "telcfg_path": str(ANALYSIS / "radio_pipeline/resources/scattering_telescopes.yaml"),
}

# (label, dsa_t, dsa_f, chime_t, chime_f). The campaign contract is dsa (2, 384)
# / chime (24, 16); "r1" is finer than the contract in frequency, and the
# numbered rows above it divide the fitted data volume further.
LADDER = [
    ("r256", 32, 1536, 384, 64),
    ("r128", 16, 1536, 192, 64),
    ("r64", 16, 768, 192, 32),
    ("r32", 8, 768, 96, 32),
    ("r16", 8, 384, 96, 16),
    ("r8", 4, 384, 48, 16),
    ("r4", 4, 192, 48, 8),
    ("r2", 2, 192, 24, 8),
    ("contract", 2, 384, 24, 16),
    ("r1", 1, 192, 12, 8),
]


def write_configs(cell, dsa_t, dsa_f, chime_t, chime_f, walks, dlogz, scan):
    cfg = cell / "configs"
    cfg.mkdir(parents=True, exist_ok=True)
    # The rwalk step count comes from the sampler resource file, not from any
    # band-config key: varying "nlive_walks" in the band YAML left nc at 36 in
    # every cell. Copy the resource per cell and edit "walks" there instead.
    sampcfg = cell / "scattering_sampler.yaml"
    src = Path(BASE["sampcfg_path"]).read_text().splitlines()
    out = []
    for line in src:
        if line.strip().startswith("walks:"):
            indent = line[: len(line) - len(line.lstrip())]
            out.append(f"{indent}walks:          {walks}")
        else:
            out.append(line)
    sampcfg.write_text("\n".join(out) + "\n")
    common = {**BASE, "dlogz": dlogz, "sampcfg_path": str(sampcfg), "model_scan": scan}
    bands = {
        "dsa": {**common, "dm_init": 262.368, "f_factor": dsa_f, "path": DSA,
                "t_factor": dsa_t, "telescope": "dsa"},
        "chime": {**common, "dm_init": 0.0, "f_factor": chime_f, "path": CHIME,
                  "t_factor": chime_t, "telescope": "chime"},
    }
    for band, c in bands.items():
        lines = [f"{k}: {json.dumps(v)}" for k, v in sorted(c.items())]
        (cfg / f"zach_{band}_run.yaml").write_text("\n".join(lines) + "\n")


def run_cell(label, dsa_t, dsa_f, chime_t, chime_f, nlive, nproc, cap_s, walks, dlogz, scan=True):
    cell = ROOT / f"{label}_n{nlive}_p{nproc}_w{walks}_d{dlogz}_s{int(scan)}"
    cell.mkdir(parents=True, exist_ok=True)
    write_configs(cell, dsa_t, dsa_f, chime_t, chime_f, walks, dlogz, scan)
    env = {**os.environ, "PYTHONPATH": str(ANALYSIS), "PYTHONDONTWRITEBYTECODE": "1",
           "FABER2026_ANALYSIS": str(ANALYSIS), "FABER2026_RUNS": str(cell)}
    cmd = [str(PY), "run_joint_fit.py", "zach", str(nlive), str(nproc),
           "--seed", "20220207", "--gain-s2", "1",
           "--components-C", "2", "--components-D", "4", "--dlogz", str(dlogz)]
    start = time.time()
    with (cell / "run.log").open("w") as log:
        try:
            rc = subprocess.run(cmd, cwd=JOINT, env=env, stdout=log,
                                stderr=subprocess.STDOUT, timeout=cap_s).returncode
        except subprocess.TimeoutExpired:
            rc = "TIMEOUT"
    elapsed = time.time() - start
    result = {
        "label": label, "nlive": nlive, "nproc": nproc, "walks": walks, "dlogz": dlogz,
        "dsa_t_factor": dsa_t, "dsa_f_factor": dsa_f,
        "chime_t_factor": chime_t, "chime_f_factor": chime_f,
        "dsa_channels": 6144 // dsa_f, "dsa_bins": 2500 // dsa_t,
        "chime_channels": 1024 // chime_f, "chime_bins": 32000 // chime_t,
        "returncode": rc, "seconds": round(elapsed, 1),
        "under_5_min": bool(rc == 0 and elapsed < 300),
        "model_scan": scan,
    }
    # Split preparation from sampling: the progress bar carries its own elapsed
    # clock, so whatever the wall clock has that the bar does not is setup.
    sampler_s = None
    text = (cell / "run.log").read_text(errors="ignore").replace("\r", "\n")
    stamps = re.findall(r"\[(\d+):(\d\d)(?::(\d\d))?<", text)
    if stamps:
        a, b, c = stamps[-1]
        sampler_s = (int(a) * 3600 + int(b) * 60 + int(c)) if c else (int(a) * 60 + int(b))
    result["sampler_seconds"] = sampler_s
    result["prep_seconds"] = round(elapsed - sampler_s, 1) if sampler_s is not None else None
    result["fitted_points"] = (result["dsa_channels"] * result["dsa_bins"]
                               + result["chime_channels"] * result["chime_bins"])
    (cell / "timing.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)
    return result


if __name__ == "__main__":
    label = sys.argv[1]
    nlive = int(sys.argv[2])
    nproc = int(sys.argv[3])
    cap = int(sys.argv[4])
    walks = int(sys.argv[5]) if len(sys.argv) > 5 else 15
    dlogz = float(sys.argv[6]) if len(sys.argv) > 6 else 0.5
    scan = (sys.argv[7] != "noscan") if len(sys.argv) > 7 else True
    row = next(r for r in LADDER if r[0] == label)
    run_cell(row[0], row[1], row[2], row[3], row[4], nlive, nproc, cap, walks, dlogz, scan)
