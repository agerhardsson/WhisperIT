#!/bin/bash
# WhisperIT launcher and utility script
# Usage: ./run.sh [setup|update|gui|cli|help] [args...]

set -e

MODE=${1:-gui}
shift || true

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if ! command -v uv >/dev/null 2>&1; then
    echo "uv is required. Install it from https://docs.astral.sh/uv/getting-started/installation/" >&2
    exit 1
fi

function setup_env() {
    uv sync
}

function update_deps() {
    uv lock --upgrade
    uv sync
}

case "$MODE" in
    setup)
        setup_env
        ;;
    update)
        update_deps
        ;;
    gui)
        uv run whisperit-gui "$@"
        ;;
    cli)
        uv run whisperit "$@"
        ;;
    help|--help|-h)
        echo "Usage: ./run.sh [setup|update|gui|cli|help] [args...]"
        echo "  setup   Create the uv environment and install dependencies"
        echo "  update  Upgrade dependencies and refresh uv.lock"
        echo "  gui     Launch GUI (default)"
        echo "  cli     Run interactive CLI or pass arguments directly [see --help]"
        echo "  help    Show this message"
        ;;
    *)
        echo "Unknown mode: $MODE"
        echo "Run ./run.sh help for usage."
        exit 1
        ;;
esac
