# Booking KHLUG - Scanner Library

USB 웹캠(HCAM01S)을 바코드/QR 스캐너로 추상화한 Rust 라이브러리(Crate)입니다.
Video4Linux(V4L2)를 통해 프레임 데이터를 가져오고, 이미지 처리 후 디코딩하여 문자열을 반환합니다.

## 기술 스택

- Language: Rust
- Camera Interface: v4l (Video4Linux bindings)
- Decoding: rxing (Pure Rust port of ZXing) or zbar-rust

## 기능

- 웹캠 장치 열기 및 설정 (해상도, 포맷)
- 프레임 캡처 및 그레이스케일 변환
- 바코드(ISBN) 및 QR 코드 디코딩
- 스캔 결과 콜백 처리

## 설치 및 의존성

Cargo.toml에 다음과 같이 로컬 경로 또는 git 저장소를 추가하여 사용합니다.

```
[dependencies]
scanner = { path = "../scanner" }
```

## 시스템 요구사항

리눅스 환경에서 v4l-utils 라이브러리가 필요할 수 있습니다.

- Alpine: apk add libv4l
- Debian/Ubuntu: apt install libv4l-dev

## 사용 예제 (Rust)

```
use scanner::Scanner;

fn main() {
    // 1. 스캐너 인스턴스 생성 (장치 경로 지정)
    let mut scanner = Scanner::new("/dev/video0").expect("카메라 열기 실패");

    // 2. 스캔 루프 시작
    scanner.start_scan(|code, code_type| {
        println!("스캔됨: [{}] {}", code_type, code);
        // 여기서 Poem 웹소켓 등으로 데이터 전송
    });

}
```
