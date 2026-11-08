#!/bin/env bash

#SBATCH --job-name=churroless_churro
#SBATCH --output=runs/churroless_churro_%j.out
#SBATCH --mail-type=ALL
#SBATCH --partition=gpu
#SBATCH --ntasks=1
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=48G
#SBATCH --gres=gpu:1
#SBATCH --time=00-04:00:00

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK}

set -xefaou pipefail

source .env
set +eu
TEMP_ARGS=("$@")
while [[ $# -gt 0 ]]; do
  case $1 in
    -c|--concurrency)
      if [[ -n "$2" ]]; then
        CHURROLESS_CONCURRENCY="$2"
        shift 2
      else
        shift 1
      fi
      ;;
    --concurrency=*)
      CHURROLESS_CONCURRENCY="${1#*=}"
      shift 1
      ;;
    -m|--model)
      if [[ -n "$2" ]]; then
        CHURROLESS_MODEL="$2"
        shift 2
      else
        shift 1
      fi
      ;;
    --model=*)
      CHURROLESS_MODEL="${1#*=}"
      shift 1
      ;;
    *)
      shift 1
      ;;
  esac
done
set -eu
set -- "${TEMP_ARGS[@]}"

module purge

set +e

module load cuda/13.0
module load cudnn/9.17/cuda13
module load python/3.12.10

set -e

JOB_ID=${SLURM_JOB_ID:-${SLURM_JOBID:-$$}}

cd $CHURROLESS_REPO_PATH

if [ ! -d ".venv" ]; then
    uv venv
    uv add --dev .
fi

uv sync

export GGML_CUDA_P2P=1

#    --split-mode tensor \
llama-server \
    --no-ui \
    --parallel $CHURROLESS_CONCURRENCY \
    -hf $CHURROLESS_MODEL \
    > runs/llama-server_${JOB_ID}.log 2>&1 \
    &


uv run churroless_churro.py "$@"

exit 0