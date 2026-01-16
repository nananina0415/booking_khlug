# Booking KHLUG - Shared Components

키오스크와 서버 웹 프론트엔드에서 공유하는 Svelte 컴포넌트입니다.

## 컴포넌트 목록

### BookCard.svelte

도서 카드 컴포넌트. 도서 정보와 대출 상태를 표시합니다.

```svelte
<BookCard
    isbn="9788966262472"
    title="러스트 프로그래밍"
    author="스티브 클라브닉"
    publisher="제이펍"
    publishedYear={2023}
    totalCount={3}
    availableCount={2}
    href="/book/9788966262472"
/>
```

### BookList.svelte

도서 목록 컴포넌트. BookCard를 그리드로 배치합니다.

```svelte
<BookList
    books={bookArray}
    getHref={(isbn) => `/book/${isbn}`}
/>
```

### QRCode.svelte

QR 코드 표시 컴포넌트. 외부 API를 통해 QR 이미지를 생성합니다.
만료 타이머 기능을 포함합니다.

```svelte
<QRCode
    data="token_string"
    size={200}
    expiresIn={10}
>
    <button slot="actions" let:expired on:click={refresh}>
        {expired ? '새로고침' : ''}
    </button>
</QRCode>
```

## 사용 방법

각 프론트엔드 프로젝트의 package.json에서 로컬 의존성으로 추가합니다.

```json
{
  "dependencies": {
    "@booking-khlug/shared": "file:../../shared"
  }
}
```

컴포넌트 import:

```typescript
import { BookCard, BookList, QRCode } from '@booking-khlug/shared/components';
```
