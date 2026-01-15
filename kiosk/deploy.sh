#!/bin/bash
set -e

# 라즈베리파이 접속 정보
RPI_USER="kiosk"
RPI_IP="${RPI_IP:-192.168.50.20}"
RPI_HOST="$RPI_USER@$RPI_IP"
RPI_PATH="/home/$RPI_USER/app"

echo "=== 라즈베리파이로 배포 ==="
echo "대상: $RPI_HOST:$RPI_PATH"
echo "비밀번호를 여러 번 입력해야 합니다."
echo ""

# 디렉토리 생성
ssh $RPI_HOST "mkdir -p $RPI_PATH/frontend"

# 바이너리 전송
echo "바이너리 전송 중..."
scp ../target/arm-unknown-linux-musleabihf/release/kiosk $RPI_HOST:$RPI_PATH/

# 프론트엔드 전송
echo "프론트엔드 전송 중..."
scp -r frontend/dist $RPI_HOST:$RPI_PATH/frontend/

# 실행 권한 부여
ssh $RPI_HOST "chmod +x $RPI_PATH/kiosk"

echo ""
echo "=== 배포 완료 ==="
echo "라즈베리파이에서 실행:"
echo "  cd $RPI_PATH && ./kiosk"
