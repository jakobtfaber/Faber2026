#!/bin/bash
#SBATCH --job-name=jtfsl
#SBATCH --partition=main
#SBATCH --mem-per-cpu=1G
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --output=/home/ubuntu/flits-runs/logs/%x_%j.out
#SBATCH --error=/home/ubuntu/flits-runs/logs/%x_%j.err
set -uo pipefail
BURST="$1"; BAND="$2"; NCHAN="$3"; GAMMA="$4"; M="$5"; TAU="$6"
ALPHA="${7:-4}"; SNR="${8:-40}"; DECORR="${9:-1}"; NLIVE="${10:-300}"; NPROC="${11:-4}"; SEED="${12:-0}"
WT=/home/ubuntu/worktrees/joint-tf-fits
export FLITS_REPO="$WT" FLITS_RUNS=/home/ubuntu/flits-runs PLPBF_OUTDIR=/home/ubuntu/flits-runs/data/scintleak
export PYTHONPATH="$WT:$WT/scattering:$WT/analysis/scattering-refit-2026-06"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export TMPDIR=/tmp MPLBACKEND=Agg
set +u
source /home/ubuntu/anaconda3/etc/profile.d/conda.sh
conda activate flits-a1-312
set -u
mkdir -p "$PLPBF_OUTDIR"
cd "$WT/analysis/scattering-refit-2026-06"
T0=$(date +%s)
echo "HOST=$(hostname) JOB=$SLURM_JOB_ID START=$(date -Iseconds) SCINTLEAK burst=$BURST band=$BAND nchan=$NCHAN gamma=$GAMMA m=$M tau=$TAU decorr=$DECORR seed=$SEED"
python -u scint_leakage_inject.py "$BURST" "$BAND" "$NCHAN" "$GAMMA" "$M" "$TAU" "$ALPHA" "$SNR" "$DECORR" "$NLIVE" "$NPROC" "$SEED"
RC=$?
echo "DONE SCINTLEAK burst=$BURST gamma=$GAMMA decorr=$DECORR RC=$RC WALL_SEC=$(( $(date +%s)-T0 )) END=$(date -Iseconds)"
exit $RC
