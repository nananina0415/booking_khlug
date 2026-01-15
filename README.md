# Booking KHLUG

Booking KHLUG는 KHLUG 동아리방을 위한 초경량, 고효율 도서 대출 관리 시스템입니다.
오래된 하드웨어(Raspberry Pi 1B+ or 2B)를 재활용하여 최신 웹 기술 기반의 키오스크를 구동하는 것을 목표로 합니다.

## 시스템 아키텍처 (Architecture)

전체 시스템은 크게 세 가지 파트로 구성됩니다.

1. Scanner: HCAM01S 카메라를 이용해 이미지를 캡처하고 바코드/QR 정보를 파싱해 전송합니다.
2. Kiosk: 라즈베리 파이에서 실행됩니다. 스캐너를 조작하고 웹 기술(HTML/CSS/JS)기반 UI를 통해 사용자와 상호작용합니다.
3. Server: 도서 정보 관리, 대출 및 반납 인증(QR 토큰 검증), 외부 API 연동을 담당합니다.

## 기술적 의사결정 (Technical Decisions)

이 프로젝트는 극한의 하드웨어 제약(RAM 512MB, Single Core)을 극복하기 위해 다음과 같은 기술 스택을 선정했습니다.

### 1. OS: Alpine Linux & Musl Libc

Why? 라즈베리 파이 OS(Raspbian)조차 무겁습니다. 부팅 직후 메모리 점유율을 50MB 이하로 유지하여 애플리케이션 가용 메모리를 확보하기 위해 Alpine Linux를 선택했습니다.

### 2. UI: Svelte + Cog (WPE WebKit)

Why? React의 Virtual DOM 연산은 라즈베리 파이 1B+에서 심각한 지연을 유발합니다. 컴파일 타임에 최적화되는 Svelte를 사용하여 런타임 오버헤드를 제거했습니다.
Why Cog? 무거운 데스크탑 환경(X11, GNOME 등)을 걷어내고, Wayland 기반의 Cage 위에서 웹 엔진만 단독으로 실행하는 Cog를 사용하여 GPU 가속을 극대화했습니다.

### 3. Backend: Rust

Why? Python이나 Node.js 런타임은 메모리를 많이 차지합니다. 시스템 리소스를 적게 쓰면서도 이미지 처리와 시리얼 통신을 고속으로 처리하기 위해 네이티브 언어인 Rust를 사용했습니다.

### 4. Scanner: HCAM01S

Why? 기존에는 Arduino Uno + OV7670를 사용하려 했지만 충분한 FPS가 나오지 않아 웹캠을 사용했습니다.

## 디렉터리 구조

- /kiosk: 라즈베리 파이용 Rust/Svelte 애플리케이션
- /scanner: HCAM01S을 스캐너로 추상화하는 러스트 라이브러리
- /server: 백엔드 API 서버
