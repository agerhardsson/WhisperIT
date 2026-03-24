echo ""
#!/bin/bash
# WhisperIT launcher and utility script
# Usage: ./run.sh [setup|update|gui|cli|help] [args...]

set -e

MODE=${1:-gui}
shift || true

ENV_NAME="whisperit"

function setup_env() {
    if ! command -v conda &> /dev/null; then
        echo "Conda is not installed. Install Miniconda first."
        exit 1
    fi
    if ! conda env list | grep -q "^${ENV_NAME}"; then
        echo "Creating conda environment '${ENV_NAME}'..."
        conda create -n "${ENV_NAME}" python=3.11 -y
    fi
    eval "$(conda shell.bash hook)"
    conda activate "${ENV_NAME}"
    pip install --upgrade pip
    pip install -r requirements.txt
}

function update_deps() {
    eval "$(conda shell.bash hook)"
    conda activate "${ENV_NAME}"
    pip install --upgrade pip
    pip install -r requirements.txt
}

case "$MODE" in
    setup)
        setup_env
        ;;
    update)
        update_deps
        ;;
    gui)
        eval "$(conda shell.bash hook)"
        conda activate "${ENV_NAME}"
        python src/gui.py "$@"
        ;;
    cli)
        eval "$(conda shell.bash hook)"
        conda activate "${ENV_NAME}"
        python src/cli.py "$@"
        ;;
    help|--help|-h)
        echo "Usage: ./run.sh [setup|update|gui|cli|help] [args...]"
        echo "  setup   Create conda env and install dependencies"
        echo "  update  Update dependencies (pip install -r requirements.txt)"
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
