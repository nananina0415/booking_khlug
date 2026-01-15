<script>
  import CameraView from './lib/CameraView.svelte';
</script>

<main>
  <h1>Booking KHLUG</h1>
  <p class="subtitle">바코드 또는 QR코드를 스캔하세요</p>
  <CameraView />
</main>

<style>
  main {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    padding: 20px;
  }

  h1 {
    margin: 0 0 8px 0;
    font-size: 1.8em;
    color: #333;
  }

  .subtitle {
    margin: 0 0 24px 0;
    color: #666;
    font-size: 1em;
  }
</style>
