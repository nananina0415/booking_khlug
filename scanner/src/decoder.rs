use crate::{CodeType, Result, ScanResult};
use rxing::{BarcodeFormat, DecodeHintType, DecodeHintValue, DecodingHintDictionary, Luma8LuminanceSource, Reader};
use rxing::multi::MultipleBarcodeReader;
use rxing::oned::MultiFormatOneDReader;
use rxing::qrcode::QRCodeReader;

/// YUYV 포맷을 그레이스케일로 변환
/// YUYV는 2픽셀당 4바이트: Y0 U Y1 V
/// Y 값만 추출하면 그레이스케일
pub fn yuyv_to_gray(data: &[u8], width: u32, height: u32) -> Vec<u8> {
    let pixel_count = (width * height) as usize;
    let mut gray = Vec::with_capacity(pixel_count);

    for i in 0..pixel_count {
        // YUYV에서 Y는 짝수 인덱스에 위치
        let yuyv_index = i * 2;
        if yuyv_index < data.len() {
            gray.push(data[yuyv_index]);
        }
    }

    gray
}

/// 그레이스케일 이미지에서 바코드/QR 디코딩
pub fn decode_image(gray: &[u8], width: u32, height: u32) -> Result<Option<ScanResult>> {
    let source = Luma8LuminanceSource::new(gray.to_vec(), width, height);

    // QR 코드 시도
    if let Some(result) = try_decode_qr(&source) {
        return Ok(Some(result));
    }

    // 바코드 시도
    if let Some(result) = try_decode_barcode(&source) {
        return Ok(Some(result));
    }

    Ok(None)
}

fn try_decode_qr(source: &Luma8LuminanceSource) -> Option<ScanResult> {
    let reader = QRCodeReader::new();
    let mut hints = DecodingHintDictionary::new();
    hints.insert(
        DecodeHintType::TRY_HARDER,
        DecodeHintValue::TryHarder(true),
    );

    let binary = rxing::common::HybridBinarizer::new(source.clone());

    reader
        .decode_with_hints(&mut binary.into(), &hints)
        .ok()
        .map(|r| ScanResult {
            code: r.getText().to_string(),
            code_type: CodeType::QrCode,
        })
}

fn try_decode_barcode(source: &Luma8LuminanceSource) -> Option<ScanResult> {
    let reader = MultiFormatOneDReader::new(&DecodingHintDictionary::new());
    let mut hints = DecodingHintDictionary::new();
    hints.insert(
        DecodeHintType::TRY_HARDER,
        DecodeHintValue::TryHarder(true),
    );
    hints.insert(
        DecodeHintType::POSSIBLE_FORMATS,
        DecodeHintValue::PossibleFormats(std::collections::HashSet::from([
            BarcodeFormat::EAN_13,
            BarcodeFormat::EAN_8,
            BarcodeFormat::CODE_128,
            BarcodeFormat::CODE_39,
        ])),
    );

    let binary = rxing::common::HybridBinarizer::new(source.clone());

    reader
        .decode_with_hints(&mut binary.into(), &hints)
        .ok()
        .map(|r| ScanResult {
            code: r.getText().to_string(),
            code_type: CodeType::Barcode,
        })
}
