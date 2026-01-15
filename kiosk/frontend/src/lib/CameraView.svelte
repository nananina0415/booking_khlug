<script>
  import { onMount, onDestroy } from 'svelte';

  let videoElement;
  let stream = null;
  let error = null;
  let ws = null;
  let lastScan = null;

  onMount(async () => {
    // 카메라 시작
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'environment'
        },
        audio: false
      });
      videoElement.srcObject = stream;
    } catch (e) {
      error = e.message;
      console.error('카메라 접근 실패:', e);
    }

    // WebSocket 연결
    connectWebSocket();
  });

  function connectWebSocket() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${location.host}/ws`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket 연결됨');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        lastScan = data;
        console.log('스캔 결과:', data);
      } catch (e) {
        console.error('메시지 파싱 오류:', e);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket 연결 종료, 재연결 시도...');
      setTimeout(connectWebSocket, 2000);
    };

    ws.onerror = (e) => {
      console.error('WebSocket 오류:', e);
    };
  }

  onDestroy(() => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
    if (ws) {
      ws.close();
    }
  });
</script>

<div class="camera-container">
  {#if error}
    <div class="error">
      <p>카메라를 열 수 없습니다</p>
      <p class="error-detail">{error}</p>
    </div>
  {:else}
    <video
      bind:this={videoElement}
      autoplay
      playsinline
      muted
    ></video>
    <div class="overlay">
      <div class="scan-guide"></div>
    </div>
  {/if}
</div>

{#if lastScan}
  <div class="scan-result">
    <span class="scan-type">{lastScan.type}</span>
    <span class="scan-code">{lastScan.code}</span>
  </div>
{/if}

<style>
  .camera-container {
    position: relative;
    width: 100%;
    max-width: 640px;
    aspect-ratio: 4 / 3;
    background: #000;
    border-radius: 8px;
    overflow: hidden;
  }

  video {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    pointer-events: none;
  }

  .scan-guide {
    width: 70%;
    height: 50%;
    border: 3px solid rgba(255, 255, 255, 0.8);
    border-radius: 12px;
    box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.3);
  }

  .error {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #fff;
    text-align: center;
    padding: 20px;
  }

  .error p {
    margin: 0;
  }

  .error-detail {
    font-size: 0.8em;
    color: #aaa;
    margin-top: 8px;
  }

  .scan-result {
    margin-top: 20px;
    padding: 16px 24px;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .scan-type {
    background: #4CAF50;
    color: #fff;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.8em;
    font-weight: bold;
  }

  .scan-code {
    font-family: monospace;
    font-size: 1.2em;
    color: #333;
  }
</style>
