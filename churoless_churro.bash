#!/bin/env bash

#SBATCH --job-name=churroless_churro
#SBATCH --output=churroless_churrol_%j.out
#SBATCH --mail-type=ALL
#SBATCH --partition=gpu
#SBATCH --ntasks=1
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=32G
#SBATCH --gres=gpu:1
#SBATCH --time=00-01:00:00

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK}

set -xefaou pipefail

source .env

module purge

set +e

module load cuda/13.0
module load cudnn/9.17/cuda13
module load nvidia-hpc-sdk/25.11
module load python/3.12.10

set -e

cd $CHURROLESS_REPO_PATH

source .venv/bin/activate

llama-server --no-ui --parallel ${CHURROLESS_CONCURRENCY:-10} -hf ${CHURROLESS_MODEL:-'mradermacher/churro-3B-GGUF:Q4_K_M'} &

sleep 80

uv run /scratch/hernandm/churro_tests/churroless_churro.py

exit 0