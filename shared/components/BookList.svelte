<script lang="ts">
    import BookCard from './BookCard.svelte';

    interface Book {
        isbn: string;
        title: string;
        author?: string | null;
        publisher?: string | null;
        published_year?: number | null;
        total_count?: number;
        available_count?: number;
    }

    export let books: Book[] = [];
    export let getHref: ((isbn: string) => string) | null = null;
</script>

<div class="book-list">
    {#each books as book (book.isbn)}
        <BookCard
            isbn={book.isbn}
            title={book.title}
            author={book.author}
            publisher={book.publisher}
            publishedYear={book.published_year}
            totalCount={book.total_count || 0}
            availableCount={book.available_count || 0}
            href={getHref ? getHref(book.isbn) : null}
        />
    {/each}
</div>

<style>
    .book-list {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 16px;
        max-width: 1200px;
        margin: 0 auto;
    }
</style>
