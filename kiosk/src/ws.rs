use futures_util::{SinkExt, StreamExt};
use poem::{
    web::websocket::{Message, WebSocket},
    IntoResponse,
};
use std::sync::Arc;
use tokio::sync::broadcast;

pub async fn ws_handler(
    ws: WebSocket,
    tx: Arc<broadcast::Sender<String>>,
) -> impl IntoResponse {
    let mut rx = tx.subscribe();

    ws.on_upgrade(move |socket| async move {
        let (mut sink, mut stream) = socket.split();

        // 스캔 결과를 클라이언트로 전송
        let send_task = tokio::spawn(async move {
            while let Ok(msg) = rx.recv().await {
                if sink.send(Message::Text(msg)).await.is_err() {
                    break;
                }
            }
        });

        // 클라이언트 메시지 수신 (연결 유지용)
        let recv_task = tokio::spawn(async move {
            while let Some(Ok(msg)) = stream.next().await {
                match msg {
                    Message::Close(_) => break,
                    Message::Ping(data) => {
                        // Pong은 자동 처리됨
                        let _ = data;
                    }
                    _ => {}
                }
            }
        });

        // 둘 중 하나가 종료되면 다른 것도 종료
        tokio::select! {
            _ = send_task => {},
            _ = recv_task => {},
        }
    })
}
