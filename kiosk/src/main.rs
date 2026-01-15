mod ws;

use poem::{
    endpoint::StaticFilesEndpoint,
    get,
    listener::TcpListener,
    Route, Server,
};
use std::sync::Arc;
use tokio::sync::broadcast;
use tracing_subscriber;

#[tokio::main]
async fn main() -> Result<(), std::io::Error> {
    tracing_subscriber::fmt::init();

    // 스캔 결과 브로드캐스트 채널
    let (tx, _rx) = broadcast::channel::<String>(16);
    let tx = Arc::new(tx);

    // 스캐너 백그라운드 스레드 시작
    let scanner_tx = tx.clone();
    std::thread::spawn(move || {
        run_scanner(scanner_tx);
    });

    let ws_tx = tx.clone();

    let app = Route::new()
        .at("/ws", get(move |ws| ws::ws_handler(ws, ws_tx.clone())))
        .nest(
            "/",
            StaticFilesEndpoint::new("./frontend/dist")
                .index_file("index.html"),
        );

    println!("Server running at http://0.0.0.0:8080");

    Server::new(TcpListener::bind("0.0.0.0:8080"))
        .run(app)
        .await
}

fn run_scanner(tx: Arc<broadcast::Sender<String>>) {
    let scanner = match scanner::Scanner::new("/dev/video0") {
        Ok(s) => s,
        Err(e) => {
            eprintln!("스캐너 초기화 실패: {}", e);
            return;
        }
    };

    println!("스캐너 시작됨");

    if let Err(e) = scanner.start_scan(|result| {
        let msg = serde_json::json!({
            "type": result.code_type.to_string(),
            "code": result.code,
        });
        let _ = tx.send(msg.to_string());
        println!("스캔됨: [{}] {}", result.code_type, result.code);
    }) {
        eprintln!("스캐너 오류: {}", e);
    }
}
