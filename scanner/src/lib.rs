mod error;
mod decoder;

pub use error::{ScannerError, Result};

use v4l::buffer::Type;
use v4l::io::mmap::Stream;
use v4l::io::traits::CaptureStream;
use v4l::video::Capture;
use v4l::{Device, FourCC};

/// 스캔된 코드의 종류
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CodeType {
    Barcode,
    QrCode,
}

impl std::fmt::Display for CodeType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            CodeType::Barcode => write!(f, "BARCODE"),
            CodeType::QrCode => write!(f, "QR"),
        }
    }
}

/// 스캔 결과
#[derive(Debug, Clone)]
pub struct ScanResult {
    pub code: String,
    pub code_type: CodeType,
}

/// 웹캠 스캐너
pub struct Scanner {
    device: Device,
    width: u32,
    height: u32,
}

impl Scanner {
    /// 새 스캐너 인스턴스 생성
    pub fn new(device_path: &str) -> Result<Self> {
        let device = Device::with_path(device_path)?;

        // 기본 해상도 설정 (640x480)
        let mut format = device.format()?;
        format.width = 640;
        format.height = 480;
        format.fourcc = FourCC::new(b"YUYV");
        device.set_format(&format)?;

        let format = device.format()?;

        Ok(Scanner {
            device,
            width: format.width,
            height: format.height,
        })
    }

    /// 해상도 설정
    pub fn set_resolution(&mut self, width: u32, height: u32) -> Result<()> {
        let mut format = self.device.format()?;
        format.width = width;
        format.height = height;
        self.device.set_format(&format)?;

        let format = self.device.format()?;
        self.width = format.width;
        self.height = format.height;

        Ok(())
    }

    /// 단일 프레임 캡처 후 디코딩 시도
    pub fn capture_and_decode(&self) -> Result<Option<ScanResult>> {
        let mut stream = Stream::with_buffers(&self.device, Type::VideoCapture, 4)?;

        let (buf, _meta) = stream.next()?;
        let gray = decoder::yuyv_to_gray(buf, self.width, self.height);

        decoder::decode_image(&gray, self.width, self.height)
    }

    /// 스캔 루프 시작 (콜백 방식)
    pub fn start_scan<F>(&self, mut callback: F) -> Result<()>
    where
        F: FnMut(ScanResult),
    {
        let mut stream = Stream::with_buffers(&self.device, Type::VideoCapture, 4)?;
        let mut last_code: Option<String> = None;

        loop {
            let (buf, _meta) = stream.next()?;
            let gray = decoder::yuyv_to_gray(buf, self.width, self.height);

            if let Ok(Some(result)) = decoder::decode_image(&gray, self.width, self.height) {
                // 중복 스캔 방지
                if last_code.as_ref() != Some(&result.code) {
                    last_code = Some(result.code.clone());
                    callback(result);
                }
            }
        }
    }

    /// 스캔 루프 (횟수 제한)
    pub fn scan_n_times<F>(&self, n: usize, mut callback: F) -> Result<()>
    where
        F: FnMut(ScanResult),
    {
        let mut stream = Stream::with_buffers(&self.device, Type::VideoCapture, 4)?;
        let mut count = 0;
        let mut last_code: Option<String> = None;

        while count < n {
            let (buf, _meta) = stream.next()?;
            let gray = decoder::yuyv_to_gray(buf, self.width, self.height);

            if let Ok(Some(result)) = decoder::decode_image(&gray, self.width, self.height) {
                if last_code.as_ref() != Some(&result.code) {
                    last_code = Some(result.code.clone());
                    callback(result);
                    count += 1;
                }
            }
        }

        Ok(())
    }
}
