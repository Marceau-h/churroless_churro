#!/bin/env bash

#SBATCH --job-name=churroless_churro
#SBATCH --output=runs/churroless_churro_%j.out
#SBATCH --mail-type=ALL
#SBATCH --partition=gpu
#SBATCH --ntasks=1
#SBATCH --nodes=1
#SBATCH --cpus-per-task=2
#SBATCH --mem-per-cpu=48G
#SBATCH --gres=gpu:2
#SBATCH --time=00-01:00:00

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK}

set -xefaou pipefail

source .env

module purge

set +e

module load cuda/13.0
module load cudnn/9.17/cuda13
#module load nvidia-hpc-sdk/25.11
module load python/3.12.10

set -e

JOB_ID=${SLURM_JOB_ID:-${SLURM_JOBID:-$$}}

cd $CHURROLESS_REPO_PATH

if [ ! -d ".venv" ]; then
  uv add --dev .
  uv venv
fi

source .venv/bin/activate

export GGML_CUDA_P2P=1

llama-server \
    --no-ui \
    --parallel ${CHURROLESS_CONCURRENCY:-10} \
    --split-mode tensor \
    -hf ${CHURROLESS_MODEL:-'mradermacher/churro-3B-GGUF:Q8_0'} \
    > runs/llama-server_${JOB_ID}.log 2>&1 \
    &


uv run churroless_churro.py

exit 0