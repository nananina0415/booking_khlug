#!/bin/bash
set -e

echo "=== Frontend 빌드 ==="
cd frontend
npm install
npm run build
cd ..

echo "=== Rust 백엔드 빌드 (ARM musl) ==="
cargo build --release --target arm-unknown-linux-musleabihf

echo "=== 빌드 완료 ==="
echo "배포 파일:"
echo "  - frontend/dist/ (정적 파일)"
echo "  - ../target/arm-unknown-linux-musleabihf/release/kiosk (바이너리)"
