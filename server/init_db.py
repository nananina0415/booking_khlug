#!/usr/bin/env python3
"""
데이터베이스 초기화 스크립트

사용법:
    python init_db.py          # 기본 초기화 (테이블 생성만)
    python init_db.py --seed   # 테스트 데이터 포함
    python init_db.py --reset  # 기존 데이터 삭제 후 초기화
"""

import argparse
import os
import sqlite3

DATABASE = os.path.join(os.path.dirname(__file__), 'data', 'booking.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'spec', 'schema.sql')


def init_db(reset: bool = False):
    """데이터베이스 초기화"""
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)

    if reset and os.path.exists(DATABASE):
        os.remove(DATABASE)
        print("기존 데이터베이스 삭제됨")

    conn = sqlite3.connect(DATABASE)

    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())

    conn.commit()
    conn.close()
    print(f"데이터베이스 초기화 완료: {DATABASE}")


def seed_db():
    """테스트 데이터 삽입"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # 사용자 추가
    users = [
        ('admin', '관리자', 'admin@khlug.org', 'MANAGER'),
        ('user1', '홍길동', 'hong@khlug.org', 'USER'),
        ('user2', '김철수', 'kim@khlug.org', 'USER'),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO user (id, name, email, role) VALUES (?, ?, ?, ?)",
        users
    )

    # 도서 추가
    books = [
        ('9788966262472', '러스트 프로그래밍', '스티브 클라브닉', '제이펍', 2023, 'ko', 520, None),
        ('9788968482519', '클린 코드', '로버트 C. 마틴', '인사이트', 2013, 'ko', 584, None),
        ('9788966261178', '자바스크립트 완벽 가이드', '데이비드 플래너건', '인사이트', 2022, 'ko', 1256, None),
        ('9791162241882', '파이썬 알고리즘 인터뷰', '박상길', '책만', 2020, 'ko', 656, None),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO book_info (isbn, title, author, publisher, published_year, language, pages, cover_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        books
    )

    # 소장 정보 추가
    collections = [
        ('9788966262472', 2, 2),
        ('9788968482519', 1, 1),
        ('9788966261178', 1, 1),
        ('9791162241882', 3, 3),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO book_collection (isbn, total_count, available_count) VALUES (?, ?, ?)",
        collections
    )

    conn.commit()
    conn.close()
    print("테스트 데이터 삽입 완료")


def main():
    parser = argparse.ArgumentParser(description='데이터베이스 초기화')
    parser.add_argument('--seed', action='store_true', help='테스트 데이터 포함')
    parser.add_argument('--reset', action='store_true', help='기존 데이터 삭제 후 초기화')
    args = parser.parse_args()

    init_db(reset=args.reset)

    if args.seed:
        seed_db()


if __name__ == '__main__':
    main()
