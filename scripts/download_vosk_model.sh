#!/usr/bin/env bash
# Download Vosk small English model for offline STT
set -euo pipefail

MODEL_NAME="vosk-model-small-en-us-0.15"
MODEL_DIR="models/vosk-model-small-en-us"
DOWNLOAD_URL="https://alphacephei.com/vosk/models/${MODEL_NAME}.zip"

echo "Checking Vosk model…"
if [ -d "$MODEL_DIR" ]; then
  echo "✅ Model already exists at $MODEL_DIR"
  exit 0
fi

mkdir -p models
echo "Downloading Vosk model from $DOWNLOAD_URL…"
curl -L "$DOWNLOAD_URL" -o /tmp/vosk-model.zip

echo "Extracting model…"
unzip -q /tmp/vosk-model.zip -d models/
mv "models/${MODEL_NAME}" "$MODEL_DIR" 2>/dev/null || true
rm -f /tmp/vosk-model.zip

echo "✅ Vosk model installed at $MODEL_DIR"
