#!/bin/sh
set -eu

ollama serve &
ollama_pid=$!

cleanup() {
  kill "$ollama_pid"
}

trap cleanup INT TERM EXIT

until ollama list >/dev/null 2>&1; do
  sleep 2
done

ollama pull "${OLLAMA_MODEL:-qwen2.5:3b}"
ollama pull "${OLLAMA_EMBED_MODEL:-nomic-embed-text}"

wait "$ollama_pid"
