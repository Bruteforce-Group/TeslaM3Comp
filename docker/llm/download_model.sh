#!/bin/bash
# Download script for Llama 3 model
# This script downloads the Llama 3 model from Hugging Face

set -e

# Configuration
MODEL_DIR="/app/models/llama3"
LOG_FILE="/app/logs/model_download.log"
HUGGINGFACE_TOKEN=${HUGGINGFACE_TOKEN:-""}
MODEL_REPO="meta-llama/Meta-Llama-3-8B"
MODEL_VARIANT="none" # Options: none, q4_0, q4_1, q5_0, q5_1, q8_0

# Create directories
mkdir -p "$MODEL_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

# Log function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log "Starting Llama 3 model download"

# Check if model already exists
if [ -f "$MODEL_DIR/ggml-model-f16.gguf" ]; then
    log "Model already exists, skipping download"
    exit 0
fi

# Check if HuggingFace token is provided
if [ -z "$HUGGINGFACE_TOKEN" ]; then
    log "Warning: HUGGINGFACE_TOKEN not provided. Will attempt to download without authentication."
    log "For Meta-Llama models, you need to accept the license on Hugging Face and provide a token."
fi

# Install git-lfs if not already installed
if ! command -v git-lfs &> /dev/null; then
    log "Installing git-lfs"
    apt-get update && apt-get install -y git-lfs
fi

# Set up git-lfs
git lfs install

# Create a temporary directory for cloning
TEMP_DIR=$(mktemp -d)
log "Created temporary directory: $TEMP_DIR"

# Clone the model repository
log "Cloning model repository: $MODEL_REPO"
if [ -z "$HUGGINGFACE_TOKEN" ]; then
    git clone "https://huggingface.co/$MODEL_REPO" "$TEMP_DIR/model"
else
    git clone "https://oauth2:$HUGGINGFACE_TOKEN@huggingface.co/$MODEL_REPO" "$TEMP_DIR/model"
fi

# Check if clone was successful
if [ $? -ne 0 ]; then
    log "Error: Failed to clone model repository"
    log "If this is a private or gated model, make sure to provide a valid HUGGINGFACE_TOKEN"
    exit 1
fi

log "Model repository cloned successfully"

# Convert model to GGUF format if needed
log "Converting model to GGUF format"
cd "$TEMP_DIR/model"

# Check if we need to quantize the model
if [ "$MODEL_VARIANT" = "none" ]; then
    log "Using full precision model (no quantization)"
    python -m llama_cpp.model_converter --outfile "$MODEL_DIR/ggml-model-f16.gguf"
else
    log "Quantizing model to $MODEL_VARIANT"
    python -m llama_cpp.model_converter --outfile "$MODEL_DIR/ggml-model-$MODEL_VARIANT.gguf" --quantize "$MODEL_VARIANT"
fi

# Check if conversion was successful
if [ $? -ne 0 ]; then
    log "Error: Failed to convert model to GGUF format"
    exit 1
fi

log "Model converted successfully"

# Copy tokenizer and model config
log "Copying tokenizer and model config"
cp tokenizer.model "$MODEL_DIR/"
cp config.json "$MODEL_DIR/"

# Clean up
log "Cleaning up temporary files"
rm -rf "$TEMP_DIR"

log "Model download and preparation completed successfully"
log "Model is ready at: $MODEL_DIR"

exit 0
