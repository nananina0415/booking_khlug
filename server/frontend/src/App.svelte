<script lang="ts">
    import BookListPage from './pages/BookListPage.svelte';
    import BookDetailPage from './pages/BookDetailPage.svelte';

    // 간단한 해시 라우터
    let currentPath = window.location.hash.slice(1) || '/';
    let params: Record<string, string> = {};

    window.addEventListener('hashchange', () => {
        currentPath = window.location.hash.slice(1) || '/';
        parseParams();
    });

    function parseParams() {
        const match = currentPath.match(/^\/book\/([^/]+)$/);
        if (match) {
            params = { isbn: match[1] };
        } else {
            params = {};
        }
    }

    parseParams();

    $: isBookList = currentPath === '/' || currentPath === '/book';
    $: isBookDetail = currentPath.startsWith('/book/') && params.isbn;
</script>

<main>
    {#if isBookList}
        <BookListPage />
    {:else if isBookDetail}
        <BookDetailPage isbn={params.isbn} />
    {:else}
        <div class="not-found">
            <h1>페이지를 찾을 수 없습니다</h1>
            <a href="#/">도서 목록으로</a>
        </div>
    {/if}
</main>

<style>
    :global(*) {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }

    :global(body) {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        background: #f5f5f5;
    }

    main {
        padding: 20px;
        min-height: 100vh;
    }

    .not-found {
        text-align: center;
        padding: 40px;
    }

    .not-found h1 {
        margin-bottom: 20px;
        color: #333;
    }

    .not-found a {
        color: #1976d2;
    }
</style>
