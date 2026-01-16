<script lang="ts">
    export let isbn: string;
    export let title: string;
    export let author: string | null = null;
    export let publisher: string | null = null;
    export let publishedYear: number | null = null;
    export let totalCount: number = 0;
    export let availableCount: number = 0;
    export let href: string | null = null;
</script>

<div class="book-card">
    {#if href}
        <a {href}>
            <h3>{title}</h3>
            <p class="author">{author || '저자 미상'}</p>
            <p class="publisher">
                {publisher || ''}
                {#if publishedYear}({publishedYear}){/if}
            </p>
            {#if availableCount > 0}
                <span class="status available">대출 가능 ({availableCount}/{totalCount})</span>
            {:else}
                <span class="status unavailable">대출 불가</span>
            {/if}
        </a>
    {:else}
        <h3>{title}</h3>
        <p class="author">{author || '저자 미상'}</p>
        <p class="publisher">
            {publisher || ''}
            {#if publishedYear}({publishedYear}){/if}
        </p>
        {#if availableCount > 0}
            <span class="status available">대출 가능 ({availableCount}/{totalCount})</span>
        {:else}
            <span class="status unavailable">대출 불가</span>
        {/if}
    {/if}
</div>

<style>
    .book-card {
        background: white;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .book-card a {
        text-decoration: none;
        color: inherit;
        display: block;
    }

    h3 {
        font-size: 16px;
        margin-bottom: 8px;
        color: #333;
    }

    p {
        font-size: 14px;
        color: #666;
        margin-bottom: 4px;
    }

    .status {
        margin-top: 8px;
        padding: 4px 8px;
        border-radius: 4px;
        display: inline-block;
        font-size: 12px;
    }

    .status.available {
        background: #e8f5e9;
        color: #2e7d32;
    }

    .status.unavailable {
        background: #ffebee;
        color: #c62828;
    }
</style>
