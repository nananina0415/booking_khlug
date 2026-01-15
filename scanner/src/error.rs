use thiserror::Error;

#[derive(Error, Debug)]
pub enum ScannerError {
    #[error("카메라 장치 오류: {0}")]
    DeviceError(#[from] v4l::Error),

    #[error("이미지 처리 오류: {0}")]
    ImageError(#[from] image::ImageError),

    #[error("디코딩 오류: {0}")]
    DecodeError(String),

    #[error("IO 오류: {0}")]
    IoError(#[from] std::io::Error),
}

pub type Result<T> = std::result::Result<T, ScannerError>;
