#!/bin/sh
set -euo pipefail

MODEL_VERSION="0.5.4"
MODEL_NAME="en_core_sci_sm-${MODEL_VERSION}"
MODEL_URL="https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v${MODEL_VERSION}/${MODEL_NAME}.tar.gz"
BASE_DIR="statement_generator/models/${MODEL_NAME}"
MODEL_DIR="${BASE_DIR}/en_core_sci_sm/${MODEL_NAME}"
MODEL_TARBALL="statement_generator/models/${MODEL_NAME}.tar.gz"

mkdir -p "${BASE_DIR}"

echo "Downloading ${MODEL_NAME}..."
curl -L -o "${MODEL_TARBALL}" "${MODEL_URL}"

echo "Extracting to ${BASE_DIR}..."
tar -xzf "${MODEL_TARBALL}" -C "${BASE_DIR}" --strip-components=1

echo "Done."
echo "Set the model path with:"
echo "  export MKSAP_NLP_MODEL=${MODEL_DIR}"
