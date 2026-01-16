-- Booking KHLUG 데이터베이스 스키마

-- 도서 정보 테이블 (정적 정보)
CREATE TABLE IF NOT EXISTS book_info (
    isbn TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT,
    publisher TEXT,
    published_year INTEGER,
    language TEXT,
    pages INTEGER,
    cover_url TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- 도서 소장 테이블 (ISBN별 보유 권수)
CREATE TABLE IF NOT EXISTS book_collection (
    isbn TEXT PRIMARY KEY,
    total_count INTEGER NOT NULL DEFAULT 1,
    available_count INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (isbn) REFERENCES book_info(isbn)
);

-- 사용자 테이블
CREATE TABLE IF NOT EXISTS user (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    role TEXT NOT NULL DEFAULT 'USER' CHECK (role IN ('USER', 'MANAGER')),
    created_at TEXT DEFAULT (datetime('now'))
);

-- 대출 테이블
CREATE TABLE IF NOT EXISTS borrow (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    isbn TEXT NOT NULL,
    user_id TEXT NOT NULL,
    borrowed_at TEXT DEFAULT (datetime('now')),
    returned_at TEXT,
    FOREIGN KEY (isbn) REFERENCES book_info(isbn),
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_borrow_isbn ON borrow(isbn);
CREATE INDEX IF NOT EXISTS idx_borrow_user_id ON borrow(user_id);
CREATE INDEX IF NOT EXISTS idx_borrow_returned_at ON borrow(returned_at);
CREATE INDEX IF NOT EXISTS idx_user_role ON user(role);
