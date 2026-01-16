# Booking KHLUG - Kiosk Client

라즈베리 파이(1B+/2B) 위에서 돌아가는 키오스크 애플리케이션입니다.
백엔드 로직은 Rust와 Poem 프레임워크를 사용하며, 프론트엔드는 Svelte로 구성됩니다.
스캐너(웹캠) 제어는 로컬 라이브러리(scanner crate)를 통해 직접 수행합니다.

## 기술 스택

- OS: Alpine Linux (armhf)
- Network: Ethernet (Direct connection to Server)
- GUI: Cage (Wayland Compositor) + Cog (Browser)
- Web Framework: Poem (Rust)
- Scanner Logic: Local Scanner Crate (V4L2 + Rxing)
- Frontend: Svelte + Vite

## 아키텍처 및 데이터 흐름

1. Poem Web Server: 로컬호스트에서 웹 서버와 웹소켓 서버를 구동합니다.
2. Scanner Thread: 백그라운드에서 웹캠 영상을 캡처하고 바코드/QR을 디코딩합니다.
3. WebSocket: 디코딩된 데이터를 Svelte UI로 실시간 전송합니다.
4. UI Update: Svelte가 데이터를 받아 화면을 갱신하고, 필요시 메인 서버로 API 요청을 보냅니다.

## 알파인 리눅스 환경 구축 (On Raspberry Pi)

1. Alpine Linux 설치: Raspberry Pi용 Alpine Linux (armhf) 이미지를 설치합니다.
2. 필수 패키지 설치:
   ```
   apk update
   apk add cage cog mesa-dri-gallium udev ttf-dejavu font-noto-cjk libv4l
   ```
4. 권한 설정: 사용자를 video, input 그룹에 추가해야 웹캠 접근이 가능합니다.
5. 자동 실행 설정: /etc/local.d/ 스크립트를 통해 부팅 시 cage cog http://localhost:8080 명령이 실행되도록 설정합니다.

## 빌드 및 배포 (Build & Deploy)

### 1. Frontend (Svelte)

공유 컴포넌트는 /shared 폴더에서 가져옵니다.

```
cd frontend
npm install   # @booking-khlug/shared 의존성 포함
npm run build
# 결과물인 'dist' 폴더는 Rust Poem 서버의 정적 파일 경로로 설정됩니다.
```

### 2. Backend (Rust)

알파인 리눅스(musl) 타겟으로 크로스 컴파일이 필요합니다.

```
# 타겟 추가

rustup target add arm-unknown-linux-musleabihf

# 빌드 (scanner 라이브러리 의존성 포함)

cargo build --release --target arm-unknown-linux-musleabihf
```

### 3. 실행

바이너리(kiosk_app)와 정적 파일들을 라즈베리 파이로 전송 후 실행합니다.
Rust 앱 내에서 서버 API 주소를 http://192.168.50.10:3000 (서버 IP)으로 설정해야 합니다.

```
./kiosk_app
```
