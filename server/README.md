# Booking KHLUG - Demo Server

프로젝트 동작 시연을 위해 제작된 데모용 백엔드 서버입니다.
라즈베리 파이 1B+/2B의 Headless 환경(터미널 모드)에서 구동되며, SQLite를 DB로 사용합니다.

## 기술 스택

- Language: Python 3
- Framework: Flask
- Database: SQLite
- Network: Dual Interface (LAN for Kiosk, Wi-Fi for Internet)
- External API: Aladin Open API, Naver Book Search API, Google, Local(Manual Data), etc...

## 네트워크 구성 (Dual Interface)

이 서버는 두 개의 네트워크 인터페이스를 동시에 관리해야 합니다.

1. eth0 (유선 LAN): 키오스크와 직결됩니다. 고정 IP를 할당합니다.
   - IP: 192.168.50.10
   - Subnet: 255.255.255.0
2. wlan0 (무선 Wi-Fi): 외부 인터넷(API 호출용)에 연결됩니다. 공유기에서 IP를 할당받습니다.

### 설정 방법 (/etc/dhcpcd.conf)

```
interface eth0
static ip_address=192.168.50.10/24

# eth0에는 gateway나 DNS를 설정하지 않음 (내부망 전용)

interface wlan0

# wlan0은 공유기 DHCP를 따르거나, 필요시 고정 IP 설정
```

## 설치 및 실행

1. 소스 코드 다운로드 및 이동
   ```
   cd server
   ```
2. 가상환경 생성 및 패키지 설치
   ```
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. 서버 실행 (포트 3000)
   ```
   python3 app.py
   ```

## 주요 API 명세 (Major API Specification)

### 1. 도서 목록 조회

- GET /api/book/
- Response: DB에 저장된 전체 도서 목록을 반환합니다.

### 2. 도서 상세 정보 조회 (ISBN)

- GET /api/book/{isbn}
- Logic:

1. 로컬 DB에 책이 있는지 확인합니다.
2. 없다면 알라딘/네이버 API를 통해 정보를 가져와 DB에 등록하고 반환합니다.
3. 있다면 DB 정보를 반환합니다.

### 3. 도서 대출

- POST /api/borrow/{isbn}
- Request Body:
  ```
  {
  "qr_token": "user_auth_token",
  "device_id": "kiosk_01"
  }
  ```
- Logic: QR 토큰으로 사용자를 인증하고, 해당 책(ISBN)을 대출 상태로 변경합니다.

### 4. 도서 반납

- POST /api/return/{isbn}
- Request Body:
  ```
  {
  "qr_token": "user_auth_token", // 반납 시에도 본인 확인이 필요한 경우
  "device_id": "kiosk_01"
  }
  ```
- Logic: 해당 책을 반납 처리합니다.

## 외부 API 설정

.env 파일을 생성하고 API 키를 설정합니다.

```
NAVER_CLIENT_ID=your_id
NAVER_CLIENT_SECRET=your_secret
ALADIN_TTB_KEY=your_key
```
