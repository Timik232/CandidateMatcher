#!/usr/bin/env bash
set -e

ollama serve &

until ollama list >/dev/null 2>&1; do
  sleep 1
done

ollama pull "$MODEL_NAME"

wait -n
