#!/usr/bin/env bash

function main {
  set -e

  uv venv
  . .venv/bin/activate
  uv sync
  uv run immich-python "$@"
}

main "$@"
