<script lang="ts">
    import { BookList } from '@booking-khlug/shared/components';
    import { onMount } from 'svelte';

    interface Book {
        isbn: string;
        title: string;
        author?: string | null;
        publisher?: string | null;
        published_year?: number | null;
        total_count?: number;
        available_count?: number;
    }

    let books: Book[] = [];
    let userId = localStorage.getItem('user_id') || '';
    let loading = true;
    let error = '';

    onMount(async () => {
        try {
            const res = await fetch('/api/book');
            if (!res.ok) throw new Error('도서 목록을 불러올 수 없습니다');
            books = await res.json();
        } catch (e) {
            error = e instanceof Error ? e.message : '오류가 발생했습니다';
        } finally {
            loading = false;
        }
    });

    function saveUserId() {
        localStorage.setItem('user_id', userId);
    }

    function getBookHref(isbn: string): string {
        return `#/book/${isbn}`;
    }
</script>

<h1>KHLUG 도서 목록</h1>

<div class="user-form">
    <input
        type="text"
        bind:value={userId}
        placeholder="사용자 ID 입력"
    />
    <button on:click={saveUserId}>저장</button>
</div>

{#if loading}
    <p class="message">로딩 중...</p>
{:else if error}
    <p class="message error">{error}</p>
{:else if books.length === 0}
    <p class="message">등록된 도서가 없습니다</p>
{:else}
    <BookList {books} getHref={getBookHref} />
{/if}

<style>
    h1 {
        text-align: center;
        margin-bottom: 20px;
        color: #333;
    }

    .user-form {
        max-width: 400px;
        margin: 0 auto 20px;
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        display: flex;
        gap: 10px;
    }

    .user-form input {
        flex: 1;
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 4px;
    }

    .user-form button {
        padding: 10px 20px;
        background: #1976d2;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
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
