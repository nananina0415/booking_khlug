<script lang="ts">
    import { QRCode } from '@booking-khlug/shared/components';
    import { onMount } from 'svelte';

    export let isbn: string;

    interface Book {
        isbn: string;
        title: string;
        author?: string | null;
        publisher?: string | null;
        published_year?: number | null;
        language?: string | null;
        pages?: number | null;
        total_count?: number;
        available_count?: number;
        borrowers?: Array<{
            user_id: string;
            user_name: string;
            borrowed_at: string;
        }>;
    }

    interface TokenResponse {
        token: string;
        expires_in: number;
    }

    let book: Book | null = null;
    let loading = true;
    let error = '';
    let userId = localStorage.getItem('user_id') || '';
    let token = '';
    let expiresIn = 0;
    let tokenLoading = false;

    onMount(async () => {
        try {
            const res = await fetch(`/api/book/${isbn}`);
            if (!res.ok) {
                if (res.status === 404) throw new Error('도서를 찾을 수 없습니다');
                throw new Error('도서 정보를 불러올 수 없습니다');
            }
            book = await res.json();

            if (userId) {
                await fetchToken();
            }
        } catch (e) {
            error = e instanceof Error ? e.message : '오류가 발생했습니다';
        } finally {
            loading = false;
        }
    });

    async function fetchToken() {
        if (!userId) return;
        tokenLoading = true;
        try {
            // 서버에서 토큰 생성 API 호출 (내부용)
            const res = await fetch('/api/auth/token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId }),
            });
            if (res.ok) {
                const data: TokenResponse = await res.json();
                token = data.token;
                expiresIn = data.expires_in;
            }
        } catch (e) {
            console.error('토큰 생성 실패:', e);
        } finally {
            tokenLoading = false;
        }
    }

    function refreshToken() {
        fetchToken();
    }
</script>

<div class="container">
    <a href="#/" class="back">← 목록으로</a>

    {#if loading}
        <p class="message">로딩 중...</p>
    {:else if error}
        <p class="message error">{error}</p>
    {:else if book}
        <div class="card">
            <h1>{book.title}</h1>
            <p class="meta">{book.author || '저자 미상'}</p>

            <div class="info">
                {#if book.publisher}
                    <p>출판사: {book.publisher}</p>
                {/if}
                {#if book.published_year}
                    <p>출판연도: {book.published_year}</p>
                {/if}
                {#if book.language}
                    <p>언어: {book.language}</p>
                {/if}
                {#if book.pages}
                    <p>페이지: {book.pages}쪽</p>
                {/if}
                <p>ISBN: {book.isbn}</p>
            </div>

            {#if (book.available_count || 0) > 0}
                <span class="status available">
                    대출 가능 ({book.available_count}/{book.total_count})
                </span>
            {:else}
                <span class="status unavailable">
                    대출 불가 (0/{book.total_count})
                </span>
            {/if}

            {#if userId}
                <div class="qr-section">
                    <h3>대출/반납용 QR 코드</h3>
                    {#if tokenLoading}
                        <p>QR 코드 생성 중...</p>
                    {:else if token}
                        <QRCode data={token} size={200} {expiresIn}>
                            <button slot="actions" let:expired on:click={refreshToken}>
                                {expired ? 'QR 새로고침' : ''}
                            </button>
                        </QRCode>
                        <p class="hint">이 QR 코드를 키오스크 스캐너에 보여주세요</p>
                    {:else}
                        <p>QR 코드를 생성할 수 없습니다</p>
                    {/if}
                </div>
            {:else}
                <div class="qr-section">
                    <p>QR 코드를 보려면 사용자 ID를 입력하세요</p>
                    <a href="#/">목록으로 돌아가기</a>
                </div>
            {/if}

            {#if book.borrowers && book.borrowers.length > 0}
                <div class="borrowers">
                    <h3>현재 대출자</h3>
                    <ul>
                        {#each book.borrowers as b}
                            <li>{b.user_name} ({b.borrowed_at})</li>
                        {/each}
                    </ul>
                </div>
            {/if}
        </div>
    {/if}
</div>

<style>
    .container {
        max-width: 600px;
        margin: 0 auto;
    }

    .back {
        display: inline-block;
        margin-bottom: 16px;
        color: #1976d2;
        text-decoration: none;
    }

    .card {
        background: white;
        border-radius: 8px;
        padding: 24px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    h1 {
        font-size: 24px;
        margin-bottom: 8px;
    }

    .meta {
        color: #666;
        margin-bottom: 16px;
    }

    .info {
        margin-bottom: 16px;
    }

    .info p {
        margin-bottom: 4px;
        color: #333;
    }

    .status {
        padding: 8px 16px;
        border-radius: 4px;
        display: inline-block;
        margin-bottom: 16px;
    }

    .status.available {
        background: #e8f5e9;
        color: #2e7d32;
    }

    .status.unavailable {
        background: #ffebee;
        color: #c62828;
    }

    .qr-section {
        text-align: center;
        padding: 20px;
        background: #fafafa;
        border-radius: 8px;
        margin-top: 16px;
    }

    .qr-section h3 {
        margin-bottom: 16px;
    }

    .qr-section button {
        margin-top: 10px;
        padding: 10px 20px;
        cursor: pointer;
        background: #1976d2;
        color: white;
        border: none;
        border-radius: 4px;
    }

    .qr-section button:empty {
        display: none;
    }

    .hint {
        margin-top: 8px;
        font-size: 14px;
        color: #666;
    }

    .borrowers {
        margin-top: 16px;
    }

    .borrowers h3 {
        font-size: 16px;
        margin-bottom: 8px;
    }

    .borrowers ul {
        list-style: none;
    }

    .borrowers li {
        padding: 8px;
        background: #f5f5f5;
        border-radius: 4px;
        margin-bottom: 4px;
    }

    .message {
        text-align: center;
        padding: 40px;
        color: #666;
    }

    .message.error {
        color: #c62828;
    }
</style>
