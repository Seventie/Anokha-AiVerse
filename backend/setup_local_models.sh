# backend/setup_local_models.sh

#!/bin/bash

echo "🚀 Setting up local AI models for interviews..."

# Create models directory
mkdir -p ./models/whisper
mkdir -p ./models/piper
mkdir -p ./interview_recordings
mkdir -p ./interview_audio

# Download Piper TTS model (lightweight, high quality)
echo "📥 Downloading Piper TTS model..."
cd ./models/piper

# Download en_US-lessac-medium (clear male voice)
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json

# Alternative voices (optional):
# en_US-amy-medium (female)
# wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx
# wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json

cd ../..

echo "✅ Whisper will auto-download on first use"
echo "✅ Piper TTS model downloaded"
echo "🎉 Setup complete!"
