#!/usr/bin/env bash
set -euo pipefail
[[ "${PREFIX:-}" == /data/data/com.termux/files/usr && "$(uname -m)" == aarch64 ]] || {
    echo "Run inside native ARM64 Termux, not a Linux container." >&2
    exit 2
}
pkg update
pkg install -y git clang cmake ninja make openssh curl
echo "Native Termux prerequisites installed. Follow nodes/redmi/README.md for reviewed llama.cpp/model selection; no container installed."
