#!/bin/bash
#SBATCH --job-name=plik
#SBATCH --partition=main
#SBATCH --mem-per-cpu=1G
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --output=/home/ubuntu/flits-runs/logs/%x_%j.out
#SBATCH --error=/home/ubuntu/flits-runs/logs/%x_%j.err
set -uo pipefail
BETA="$1"; TAU="$2"; W="$3"; AMP="$4"; DT="$5"; NLIVE="${6:-300}"; NPROC="${7:-2}"; SEED="${8:-0}"
WT=/home/ubuntu/worktrees/joint-tf-fits; REFIT=$WT/analysis/scattering-refit-2026-06
export FLITS_RUNS=/home/ubuntu/flits-runs
export PYTHONPATH="$WT:$WT/scattering:$REFIT"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export TMPDIR=/tmp MPLBACKEND=Agg
set +u; source /home/ubuntu/anaconda3/etc/profile.d/conda.sh; conda activate flits-a1-312; set -u
cd "$REFIT"
T0=$(date +%s)
echo "HOST=$(hostname) JOB=$SLURM_JOB_ID BETA=$BETA TAU=$TAU W=$W AMP=$AMP DT=$DT NLIVE=$NLIVE"
python -u plpbf_leakage.py "$BETA" "$TAU" "$W" "$AMP" "$DT" "$NLIVE" "$NPROC" "$SEED"
echo "DONE LEAKAGE amp=$AMP dt=$DT RC=$? WALL=$(( $(date +%s)-T0 ))"
