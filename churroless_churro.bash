#!/bin/env bash

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

cd "$CHURROLESS_REPO_PATH"

source .venv/bin/activate

llama-server \
    --port 9931 \
    --parallel ${CHURROLESS_CONCURRENCY:-10} \
    -hf ${CHURROLESS_MODEL:-'mradermacher/churro-3B-GGUF:IQ4_XS'} &

LLAMA_PID=$!

trap 'kill "$LLAMA_PID" 2>/dev/null || true' EXIT

uv run churroless_churro.py "$@"

exit 0