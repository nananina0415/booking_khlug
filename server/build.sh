#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "=== Server 코드 생성 ==="

# 가상환경 확인
if [ ! -d "venv" ]; then
    echo "가상환경 생성 중..."
    python3 -m venv venv
fi

source venv/bin/activate

# 빌드 의존성 설치
echo "빌드 의존성 설치 중..."
pip install -q openapi-generator-cli datamodel-code-generator

# generated 폴더 초기화
rm -rf generated
mkdir -p generated

# 1. OpenAPI에서 Flask 서버 코드 생성
echo "OpenAPI → Flask 코드 생성 중..."
openapi-generator-cli generate \
    -i spec/openapi.yaml \
    -g python-flask \
    -o generated/api \
    --additional-properties=packageName=api,pythonSrcRoot=. \
    --global-property=models,apis,supportingFiles=util.py:typing_utils.py

# 2. OpenAPI 스키마에서 Pydantic 모델 생성 (검증용)
echo "OpenAPI → Pydantic 모델 생성 중..."
datamodel-codegen \
    --input spec/openapi.yaml \
    --input-file-type openapi \
    --output generated/models.py \
    --output-model-type dataclasses.dataclass

# 3. SQLite DB 초기화
echo "SQLite DB 초기화 중..."
if [ ! -f "data/booking.db" ]; then
    mkdir -p data
    sqlite3 data/booking.db < spec/schema.sql
    echo "DB 생성 완료: data/booking.db"
else
    echo "DB가 이미 존재합니다: data/booking.db"
fi

echo ""
echo "=== 빌드 완료 ==="
echo "생성된 파일:"
echo "  - generated/api/     (Flask 라우트 및 모델)"
echo "  - generated/models.py (Pydantic 모델)"
echo "  - data/booking.db    (SQLite DB)"
echo ""
echo "서버 실행: python3 app.py"
