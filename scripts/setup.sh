#!/usr/bin/env bash
# JARVIS Prime setup script — installs dependencies and initializes the project
set -euo pipefail

echo ""
echo "  ╔══════════════════════════════════╗"
echo "  ║   JARVIS Prime — Setup Script    ║"
echo "  ╚══════════════════════════════════╝"
echo ""

# Ensure Python >= 3.11
python3 -c "import sys; sys.exit(0) if sys.version_info >= (3, 11) else sys.exit(1)" || {
  echo "❌ Python 3.11+ is required."
  exit 1
}

echo "✅ Python version OK"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment…"
  python3 -m venv .venv
fi

echo "Activating virtual environment…"
source .venv/bin/activate || source .venv/Scripts/activate 2>/dev/null || true

# Install base dependencies
echo "Installing dependencies…"
pip install --upgrade pip --quiet
pip install -e ".[voice]" --quiet || pip install -r requirements.txt --quiet

# Copy .env if not present
if [ ! -f ".env" ]; then
  cp configs/.env.example .env
  echo "✅ .env created from configs/.env.example — please fill in your API keys."
fi

# Create data directories
mkdir -p data/memory data/chromadb models

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your API keys (GROQ_API_KEY, OPENROUTER_API_KEY)"
echo "  2. Run: make run       (CLI)"
echo "  3. Run: make api       (FastAPI server)"
echo "  4. Run: make test      (test suite)"
echo "  (Optional) bash scripts/download_vosk_model.sh  # for voice support"
echo ""
