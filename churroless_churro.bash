#!/bin/env bash

set -xefaou pipefail

source .env

cd "$CHURROLESS_REPO_PATH"

source .venv/bin/activate

llama-server --parallel ${CHURROLESS_CONCURRENCY:-10} \
    -hf ${CHURROLESS_MODEL:-'mradermacher/churro-3B-GGUF:Q4_K_M'} &

uv run churroless_churro.py

exit 0