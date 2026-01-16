<script lang="ts">
    export let data: string;
    export let size: number = 200;
    export let expiresIn: number = 0;

    let remaining = expiresIn;
    let expired = false;

    $: if (expiresIn > 0) {
        remaining = expiresIn;
        expired = false;
        const interval = setInterval(() => {
            remaining--;
            if (remaining <= 0) {
                clearInterval(interval);
                expired = true;
            }
        }, 1000);
    }

    $: qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encodeURIComponent(data)}`;
</script>

<div class="qr-container">
    {#if !expired}
        <img src={qrUrl} alt="QR Code" width={size} height={size} />
        {#if expiresIn > 0}
            <p class="timer">{remaining}초</p>
        {/if}
    {:else}
        <div class="expired" style="width: {size}px; height: {size}px;">
            <p>만료됨</p>
        </div>
    {/if}
    <slot name="actions" {expired} />
</div>

<style>
    .qr-container {
        text-align: center;
    }

    img {
        display: block;
        margin: 0 auto;
    }

    .timer {
        margin-top: 8px;
        font-size: 24px;
        font-weight: bold;
        color: #c62828;
    }

    .expired {
        display: flex;
        align-items: center;
        justify-content: center;
        background: #f5f5f5;
        border-radius: 8px;
        margin: 0 auto;
    }

    .expired p {
        color: #999;
        font-size: 18px;
    }
</style>
