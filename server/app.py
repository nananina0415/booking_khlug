"""
Booking KHLUG Server

이 파일은 생성된 코드를 연결하고 비즈니스 로직을 구현합니다.
generated/ 폴더의 코드는 직접 수정하지 마세요.
"""

import os
import sqlite3
import secrets
import time
from flask import Flask, jsonify, request, g, render_template_string, redirect
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

DATABASE = os.path.join(os.path.dirname(__file__), 'data', 'booking.db')
TOKEN_TIMEOUT = 10  # QR 토큰 유효 시간 (초)

# =============================================================================
# QR 토큰 메모리 저장소
# =============================================================================
# { token: { user_id, created_at, expires_at } }
_token_store: dict[str, dict] = {}


def _cleanup_expired_tokens():
    """만료된 토큰 정리"""
    now = time.time()
    expired = [t for t, v in _token_store.items() if v['expires_at'] < now]
    for t in expired:
        del _token_store[t]


def create_token(user_id: str) -> tuple[str, int]:
    """토큰 생성 (10초 유효)"""
    _cleanup_expired_tokens()
    token = secrets.token_urlsafe(16)
    now = time.time()
    _token_store[token] = {
        'user_id': user_id,
        'created_at': now,
        'expires_at': now + TOKEN_TIMEOUT
    }
    return token, TOKEN_TIMEOUT


def verify_token(token: str) -> str | None:
    """토큰 검증, 유효하면 user_id 반환 후 삭제 (일회용)"""
    _cleanup_expired_tokens()
    if token not in _token_store:
        return None
    user_id = _token_store[token]['user_id']
    del _token_store[token]
    return user_id


def verify_manager_token(token: str) -> tuple[str | None, str | None]:
    """매니저 토큰 검증, (user_id, error_type) 반환"""
    user_id = verify_token(token)
    if user_id is None:
        return None, "unauthorized"

    db = get_db()
    cursor = db.execute("SELECT role FROM user WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if user is None:
        return None, "not_found"
    if user['role'] != 'MANAGER':
        return None, "forbidden"

    return user_id, None


# =============================================================================
# 데이터베이스
# =============================================================================

def get_db():
    """데이터베이스 연결 가져오기"""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    """요청 종료 시 DB 연결 닫기"""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def get_book_with_collection(db, isbn: str) -> dict | None:
    """도서 정보 + 소장 현황 조회"""
    cursor = db.execute("""
        SELECT bi.*, bc.total_count, bc.available_count
        FROM book_info bi
        LEFT JOIN book_collection bc ON bi.isbn = bc.isbn
        WHERE bi.isbn = ?
    """, (isbn,))
    row = cursor.fetchone()
    return dict(row) if row else None


def get_book_borrowers(db, isbn: str) -> list[dict]:
    """해당 도서의 현재 대출자 목록"""
    cursor = db.execute("""
        SELECT b.user_id, u.name as user_name, b.borrowed_at
        FROM borrow b
        JOIN user u ON b.user_id = u.id
        WHERE b.isbn = ? AND b.returned_at IS NULL
    """, (isbn,))
    return [dict(row) for row in cursor.fetchall()]


# =============================================================================
# HTML 템플릿
# =============================================================================

BOOK_LIST_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KHLUG 도서 목록</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; padding: 20px; }
        h1 { text-align: center; margin-bottom: 20px; color: #333; }
        .books { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; max-width: 1200px; margin: 0 auto; }
        .book { background: white; border-radius: 8px; padding: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .book h3 { font-size: 16px; margin-bottom: 8px; }
        .book p { font-size: 14px; color: #666; margin-bottom: 4px; }
        .book .status { margin-top: 8px; padding: 4px 8px; border-radius: 4px; display: inline-block; font-size: 12px; }
        .book .status.available { background: #e8f5e9; color: #2e7d32; }
        .book .status.unavailable { background: #ffebee; color: #c62828; }
        .book a { text-decoration: none; color: inherit; display: block; }
        .login-form { max-width: 400px; margin: 0 auto 20px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .login-form input { width: 100%; padding: 10px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 4px; }
        .login-form button { width: 100%; padding: 10px; background: #1976d2; color: white; border: none; border-radius: 4px; cursor: pointer; }
    </style>
</head>
<body>
    <h1>KHLUG 도서 목록</h1>
    <div class="login-form">
        <input type="text" id="user_id" placeholder="사용자 ID 입력" value="{{ user_id }}">
        <button onclick="saveUserId()">저장</button>
    </div>
    <div class="books">
        {% for book in books %}
        <div class="book">
            <a href="/book/{{ book.isbn }}?user_id={{ user_id }}">
                <h3>{{ book.title }}</h3>
                <p>{{ book.author or '저자 미상' }}</p>
                <p>{{ book.publisher or '' }} {% if book.published_year %}({{ book.published_year }}){% endif %}</p>
                {% if book.available_count and book.available_count > 0 %}
                <span class="status available">대출 가능 ({{ book.available_count }}/{{ book.total_count }})</span>
                {% else %}
                <span class="status unavailable">대출 불가</span>
                {% endif %}
            </a>
        </div>
        {% endfor %}
    </div>
    <script>
        function saveUserId() {
            const userId = document.getElementById('user_id').value;
            localStorage.setItem('user_id', userId);
            location.reload();
        }
        window.onload = function() {
            const saved = localStorage.getItem('user_id');
            if (saved && !document.getElementById('user_id').value) {
                document.getElementById('user_id').value = saved;
            }
        }
    </script>
</body>
</html>
"""

BOOK_DETAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ book.title }} - KHLUG</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; }
        .back { display: inline-block; margin-bottom: 16px; color: #1976d2; text-decoration: none; }
        .card { background: white; border-radius: 8px; padding: 24px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { font-size: 24px; margin-bottom: 8px; }
        .meta { color: #666; margin-bottom: 16px; }
        .info { margin-bottom: 16px; }
        .info p { margin-bottom: 4px; }
        .status { padding: 8px 16px; border-radius: 4px; display: inline-block; margin-bottom: 16px; }
        .status.available { background: #e8f5e9; color: #2e7d32; }
        .status.unavailable { background: #ffebee; color: #c62828; }
        .qr-section { text-align: center; padding: 20px; background: #fafafa; border-radius: 8px; margin-top: 16px; }
        .qr-section h3 { margin-bottom: 16px; }
        .qr-section img { max-width: 200px; }
        .qr-section p { margin-top: 8px; font-size: 14px; color: #666; }
        .timer { font-size: 24px; color: #c62828; font-weight: bold; }
        .borrowers { margin-top: 16px; }
        .borrowers h3 { font-size: 16px; margin-bottom: 8px; }
        .borrowers ul { list-style: none; }
        .borrowers li { padding: 8px; background: #f5f5f5; border-radius: 4px; margin-bottom: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/book/?user_id={{ user_id }}" class="back">← 목록으로</a>
        <div class="card">
            <h1>{{ book.title }}</h1>
            <p class="meta">{{ book.author or '저자 미상' }}</p>
            <div class="info">
                {% if book.publisher %}<p>출판사: {{ book.publisher }}</p>{% endif %}
                {% if book.published_year %}<p>출판연도: {{ book.published_year }}</p>{% endif %}
                {% if book.language %}<p>언어: {{ book.language }}</p>{% endif %}
                {% if book.pages %}<p>페이지: {{ book.pages }}쪽</p>{% endif %}
                <p>ISBN: {{ book.isbn }}</p>
            </div>
            {% if book.available_count and book.available_count > 0 %}
            <span class="status available">대출 가능 ({{ book.available_count }}/{{ book.total_count }})</span>
            {% else %}
            <span class="status unavailable">대출 불가 (0/{{ book.total_count }})</span>
            {% endif %}

            {% if user_id and user %}
            <div class="qr-section">
                <h3>대출/반납용 QR 코드</h3>
                <div id="qr-container">
                    <img id="qr-img" src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={{ token }}" alt="QR Code">
                    <p>이 QR 코드를 키오스크 스캐너에 보여주세요</p>
                    <p class="timer" id="timer">{{ expires_in }}초</p>
                </div>
                <button onclick="refreshToken()" id="refresh-btn" style="display:none; margin-top:10px; padding:10px 20px; cursor:pointer;">QR 새로고침</button>
            </div>
            {% else %}
            <div class="qr-section">
                <p>QR 코드를 보려면 사용자 ID를 입력하세요</p>
                <a href="/book/?user_id=" style="color:#1976d2;">목록으로 돌아가기</a>
            </div>
            {% endif %}

            {% if book.borrowers and book.borrowers|length > 0 %}
            <div class="borrowers">
                <h3>현재 대출자</h3>
                <ul>
                    {% for b in book.borrowers %}
                    <li>{{ b.user_name }} ({{ b.borrowed_at }})</li>
                    {% endfor %}
                </ul>
            </div>
            {% endif %}
        </div>
    </div>
    <script>
        let remaining = {{ expires_in }};
        const timer = document.getElementById('timer');
        const refreshBtn = document.getElementById('refresh-btn');

        const interval = setInterval(() => {
            remaining--;
            if (remaining <= 0) {
                clearInterval(interval);
                timer.textContent = '만료됨';
                refreshBtn.style.display = 'inline-block';
            } else {
                timer.textContent = remaining + '초';
            }
        }, 1000);

        function refreshToken() {
            location.reload();
        }
    </script>
</body>
</html>
"""

# =============================================================================
# API 엔드포인트
# =============================================================================

@app.route("/")
def index():
    return jsonify({"message": "Booking KHLUG Server", "version": "1.0.0"})


# =============================================================================
# 웹 페이지 (사용자용)
# =============================================================================

@app.route("/book/")
def book_list_page():
    """도서 목록 웹 페이지"""
    user_id = request.args.get("user_id", "")
    db = get_db()
    cursor = db.execute("""
        SELECT bi.*, bc.total_count, bc.available_count
        FROM book_info bi
        LEFT JOIN book_collection bc ON bi.isbn = bc.isbn
    """)
    books = [dict(row) for row in cursor.fetchall()]
    return render_template_string(BOOK_LIST_TEMPLATE, books=books, user_id=user_id)


@app.route("/book/<isbn>")
def book_detail_page(isbn):
    """도서 상세 웹 페이지 (QR 코드 포함)"""
    user_id = request.args.get("user_id", "")
    db = get_db()

    # 도서 정보 조회
    book = get_book_with_collection(db, isbn)
    if book is None:
        return render_template_string("""
            <!DOCTYPE html>
            <html><head><title>도서를 찾을 수 없음</title></head>
            <body><h1>도서를 찾을 수 없습니다</h1><a href="/book/">목록으로</a></body>
            </html>
        """), 404

    book['borrowers'] = get_book_borrowers(db, isbn)

    # 사용자 확인 및 토큰 생성
    user = None
    token = ""
    expires_in = 0

    if user_id:
        cursor = db.execute("SELECT * FROM user WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if user:
            user = dict(user)
            token, expires_in = create_token(user_id)

    return render_template_string(
        BOOK_DETAIL_TEMPLATE,
        book=book,
        user_id=user_id,
        user=user,
        token=token,
        expires_in=expires_in
    )


# =============================================================================
# 사용자 관리 페이지 (매니저 전용)
# =============================================================================

USER_MANAGEMENT_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>사용자 관리 - KHLUG</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; padding: 20px; }
        .container { max-width: 900px; margin: 0 auto; }
        h1 { text-align: center; margin-bottom: 20px; color: #333; }
        .back { display: inline-block; margin-bottom: 16px; color: #1976d2; text-decoration: none; }
        .card { background: white; border-radius: 8px; padding: 24px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .form-group { margin-bottom: 16px; }
        .form-group label { display: block; margin-bottom: 4px; font-weight: 500; }
        .form-group input, .form-group select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        .btn { padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
        .btn-primary { background: #1976d2; color: white; }
        .btn-danger { background: #c62828; color: white; }
        .btn:hover { opacity: 0.9; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #f5f5f5; font-weight: 500; }
        .role-tag { padding: 4px 8px; border-radius: 4px; font-size: 12px; }
        .role-tag.manager { background: #e3f2fd; color: #1565c0; }
        .role-tag.user { background: #f5f5f5; color: #666; }
        .error { color: #c62828; margin-bottom: 16px; padding: 12px; background: #ffebee; border-radius: 4px; }
        .success { color: #2e7d32; margin-bottom: 16px; padding: 12px; background: #e8f5e9; border-radius: 4px; }
        .login-section { text-align: center; padding: 40px; }
        .login-section input { max-width: 300px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/book/" class="back">← 도서 목록으로</a>
        <h1>사용자 관리</h1>

        {% if not manager %}
        <div class="card login-section">
            <h3>매니저 로그인 필요</h3>
            <p style="margin: 16px 0; color: #666;">사용자 관리는 매니저만 접근할 수 있습니다.</p>
            <form method="GET" action="/user/">
                <input type="text" name="manager_id" placeholder="매니저 ID 입력" required>
                <br><br>
                <button type="submit" class="btn btn-primary">로그인</button>
            </form>
        </div>
        {% else %}

        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        {% if success %}
        <div class="success">{{ success }}</div>
        {% endif %}

        <div class="card">
            <h3 style="margin-bottom: 16px;">새 사용자 추가</h3>
            <form method="POST" action="/user/add?manager_id={{ manager.id }}">
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr auto; gap: 12px; align-items: end;">
                    <div class="form-group" style="margin:0;">
                        <label>ID *</label>
                        <input type="text" name="id" required placeholder="사용자 ID">
                    </div>
                    <div class="form-group" style="margin:0;">
                        <label>이름 *</label>
                        <input type="text" name="name" required placeholder="이름">
                    </div>
                    <div class="form-group" style="margin:0;">
                        <label>역할</label>
                        <select name="role">
                            <option value="USER">일반 사용자</option>
                            <option value="MANAGER">매니저</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary">추가</button>
                </div>
            </form>
        </div>

        <div class="card">
            <h3 style="margin-bottom: 16px;">사용자 목록 ({{ users|length }}명)</h3>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>이름</th>
                        <th>역할</th>
                        <th>가입일</th>
                        <th>액션</th>
                    </tr>
                </thead>
                <tbody>
                    {% for user in users %}
                    <tr>
                        <td>{{ user.id }}</td>
                        <td>{{ user.name }}</td>
                        <td>
                            <span class="role-tag {{ 'manager' if user.role == 'MANAGER' else 'user' }}">
                                {{ '매니저' if user.role == 'MANAGER' else '사용자' }}
                            </span>
                        </td>
                        <td>{{ user.created_at[:10] if user.created_at else '-' }}</td>
                        <td>
                            {% if user.id != manager.id %}
                            <form method="POST" action="/user/delete/{{ user.id }}?manager_id={{ manager.id }}" style="display:inline;" onsubmit="return confirm('정말 삭제하시겠습니까?');">
                                <button type="submit" class="btn btn-danger" style="padding: 6px 12px; font-size: 12px;">삭제</button>
                            </form>
                            {% else %}
                            <span style="color: #999; font-size: 12px;">현재 로그인</span>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

BOOK_MANAGEMENT_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>도서 관리 - KHLUG</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; padding: 20px; }
        .container { max-width: 1000px; margin: 0 auto; }
        h1 { text-align: center; margin-bottom: 20px; color: #333; }
        .back { display: inline-block; margin-bottom: 16px; color: #1976d2; text-decoration: none; }
        .nav { margin-bottom: 20px; }
        .nav a { margin-right: 16px; color: #1976d2; text-decoration: none; }
        .card { background: white; border-radius: 8px; padding: 24px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .form-group { margin-bottom: 16px; }
        .form-group label { display: block; margin-bottom: 4px; font-weight: 500; }
        .form-group input, .form-group select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        .form-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }
        .btn { padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
        .btn-primary { background: #1976d2; color: white; }
        .btn-danger { background: #c62828; color: white; }
        .btn-sm { padding: 6px 12px; font-size: 12px; }
        .btn:hover { opacity: 0.9; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #f5f5f5; font-weight: 500; }
        .status { padding: 4px 8px; border-radius: 4px; font-size: 12px; }
        .status.available { background: #e8f5e9; color: #2e7d32; }
        .status.unavailable { background: #ffebee; color: #c62828; }
        .error { color: #c62828; margin-bottom: 16px; padding: 12px; background: #ffebee; border-radius: 4px; }
        .success { color: #2e7d32; margin-bottom: 16px; padding: 12px; background: #e8f5e9; border-radius: 4px; }
        .login-section { text-align: center; padding: 40px; }
        .login-section input { max-width: 300px; margin-bottom: 10px; }
        .actions { display: flex; gap: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="nav">
            <a href="/book/">← 도서 목록</a>
            <a href="/user/?manager_id={{ manager.id if manager else '' }}">사용자 관리</a>
        </div>
        <h1>도서 관리</h1>

        {% if not manager %}
        <div class="card login-section">
            <h3>매니저 로그인 필요</h3>
            <p style="margin: 16px 0; color: #666;">도서 관리는 매니저만 접근할 수 있습니다.</p>
            <form method="GET" action="/manage/book/">
                <input type="text" name="manager_id" placeholder="매니저 ID 입력" required>
                <br><br>
                <button type="submit" class="btn btn-primary">로그인</button>
            </form>
        </div>
        {% else %}

        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        {% if success %}
        <div class="success">{{ success }}</div>
        {% endif %}

        <div class="card">
            <h3 style="margin-bottom: 16px;">도서 목록 ({{ books|length }}권)</h3>
            <table>
                <thead>
                    <tr>
                        <th>ISBN</th>
                        <th>제목</th>
                        <th>저자</th>
                        <th>출판사</th>
                        <th>수량</th>
                        <th>상태</th>
                        <th>액션</th>
                    </tr>
                </thead>
                <tbody>
                    {% for book in books %}
                    <tr>
                        <td style="font-size: 12px;">{{ book.isbn }}</td>
                        <td>{{ book.title }}</td>
                        <td>{{ book.author or '-' }}</td>
                        <td>{{ book.publisher or '-' }}</td>
                        <td>{{ book.available_count or 0 }}/{{ book.total_count or 0 }}</td>
                        <td>
                            {% if book.available_count and book.available_count > 0 %}
                            <span class="status available">대출가능</span>
                            {% else %}
                            <span class="status unavailable">대출불가</span>
                            {% endif %}
                        </td>
                        <td class="actions">
                            <a href="/manage/book/{{ book.isbn }}/edit?manager_id={{ manager.id }}" class="btn btn-primary btn-sm">수정</a>
                            {% if book.available_count == book.total_count %}
                            <form method="POST" action="/manage/book/{{ book.isbn }}/delete?manager_id={{ manager.id }}" style="display:inline;" onsubmit="return confirm('정말 삭제하시겠습니까?');">
                                <button type="submit" class="btn btn-danger btn-sm">삭제</button>
                            </form>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

BOOK_EDIT_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>도서 수정 - KHLUG</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; }
        h1 { text-align: center; margin-bottom: 20px; color: #333; }
        .back { display: inline-block; margin-bottom: 16px; color: #1976d2; text-decoration: none; }
        .card { background: white; border-radius: 8px; padding: 24px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .form-group { margin-bottom: 16px; }
        .form-group label { display: block; margin-bottom: 4px; font-weight: 500; }
        .form-group input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        .form-group input:disabled { background: #f5f5f5; }
        .btn { padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
        .btn-primary { background: #1976d2; color: white; }
        .btn:hover { opacity: 0.9; }
        .error { color: #c62828; margin-bottom: 16px; padding: 12px; background: #ffebee; border-radius: 4px; }
        .info { color: #666; font-size: 12px; margin-top: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/manage/book/?manager_id={{ manager.id }}" class="back">← 도서 관리로</a>
        <h1>도서 정보 수정</h1>

        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}

        <div class="card">
            <form method="POST" action="/manage/book/{{ book.isbn }}/edit?manager_id={{ manager.id }}">
                <div class="form-group">
                    <label>ISBN</label>
                    <input type="text" value="{{ book.isbn }}" disabled>
                </div>
                <div class="form-group">
                    <label>제목 *</label>
                    <input type="text" name="title" value="{{ book.title }}" required>
                </div>
                <div class="form-group">
                    <label>저자</label>
                    <input type="text" name="author" value="{{ book.author or '' }}">
                </div>
                <div class="form-group">
                    <label>출판사</label>
                    <input type="text" name="publisher" value="{{ book.publisher or '' }}">
                </div>
                <div class="form-group">
                    <label>출판연도</label>
                    <input type="number" name="published_year" value="{{ book.published_year or '' }}">
                </div>
                <div class="form-group">
                    <label>총 수량</label>
                    <input type="number" name="total_count" value="{{ book.total_count or 1 }}" min="{{ (book.total_count or 0) - (book.available_count or 0) }}">
                    <p class="info">현재 대출 중: {{ (book.total_count or 0) - (book.available_count or 0) }}권 (이보다 적게 설정 불가)</p>
                </div>
                <div class="form-group">
                    <label>페이지</label>
                    <input type="number" name="pages" value="{{ book.pages or '' }}">
                </div>
                <button type="submit" class="btn btn-primary">저장</button>
            </form>
        </div>
    </div>
</body>
</html>
"""


@app.route("/manage/book/")
def book_management_page():
    """도서 관리 웹 페이지 (매니저 전용)"""
    manager_id = request.args.get("manager_id", "")
    error = request.args.get("error", "")
    success = request.args.get("success", "")

    db = get_db()
    manager = None
    books = []

    if manager_id:
        cursor = db.execute("SELECT * FROM user WHERE id = ? AND role = 'MANAGER'", (manager_id,))
        row = cursor.fetchone()
        if row:
            manager = dict(row)
            cursor = db.execute("""
                SELECT bi.*, bc.total_count, bc.available_count
                FROM book_info bi
                LEFT JOIN book_collection bc ON bi.isbn = bc.isbn
                ORDER BY bi.title
            """)
            books = [dict(r) for r in cursor.fetchall()]
        else:
            error = "매니저 권한이 없거나 존재하지 않는 사용자입니다."

    return render_template_string(
        BOOK_MANAGEMENT_TEMPLATE,
        manager=manager,
        books=books,
        error=error,
        success=success
    )


@app.route("/manage/book/<isbn>/edit", methods=["GET", "POST"])
def book_edit_page(isbn):
    """도서 수정 페이지"""
    manager_id = request.args.get("manager_id", "")

    if not manager_id:
        return redirect("/manage/book/?error=매니저 로그인이 필요합니다")

    db = get_db()

    # 매니저 권한 확인
    cursor = db.execute("SELECT * FROM user WHERE id = ? AND role = 'MANAGER'", (manager_id,))
    row = cursor.fetchone()
    if not row:
        return redirect("/manage/book/?error=매니저 권한이 없습니다")
    manager = dict(row)

    # 도서 조회
    book = get_book_with_collection(db, isbn)
    if book is None:
        return redirect(f"/manage/book/?manager_id={manager_id}&error=도서를 찾을 수 없습니다")

    error = ""

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            error = "제목은 필수입니다"
        else:
            # book_info 업데이트
            db.execute("""
                UPDATE book_info SET
                    title = ?,
                    author = ?,
                    publisher = ?,
                    published_year = ?,
                    pages = ?
                WHERE isbn = ?
            """, (
                title,
                request.form.get("author", "").strip() or None,
                request.form.get("publisher", "").strip() or None,
                request.form.get("published_year") or None,
                request.form.get("pages") or None,
                isbn
            ))

            # total_count 업데이트
            new_total = request.form.get("total_count")
            if new_total:
                new_total = int(new_total)
                current_borrowed = (book.get("total_count") or 0) - (book.get("available_count") or 0)
                if new_total < current_borrowed:
                    error = f"대출 중인 책({current_borrowed}권)보다 적게 설정할 수 없습니다"
                else:
                    new_available = new_total - current_borrowed
                    db.execute("UPDATE book_collection SET total_count = ?, available_count = ? WHERE isbn = ?",
                               (new_total, new_available, isbn))

            if not error:
                db.commit()
                return redirect(f"/manage/book/?manager_id={manager_id}&success=도서 정보가 수정되었습니다")

        # 변경사항 롤백하고 최신 정보 다시 조회
        book = get_book_with_collection(db, isbn)

    return render_template_string(
        BOOK_EDIT_TEMPLATE,
        manager=manager,
        book=book,
        error=error
    )


@app.route("/manage/book/<isbn>/delete", methods=["POST"])
def book_delete_action(isbn):
    """도서 삭제 액션"""
    manager_id = request.args.get("manager_id", "")

    if not manager_id:
        return redirect("/manage/book/?error=매니저 로그인이 필요합니다")

    db = get_db()

    # 매니저 권한 확인
    cursor = db.execute("SELECT role FROM user WHERE id = ?", (manager_id,))
    row = cursor.fetchone()
    if not row or row['role'] != 'MANAGER':
        return redirect("/manage/book/?error=매니저 권한이 없습니다")

    # 도서 확인
    book = get_book_with_collection(db, isbn)
    if book is None:
        return redirect(f"/manage/book/?manager_id={manager_id}&error=도서를 찾을 수 없습니다")

    # 대출 중인지 확인
    borrowed = (book.get("total_count") or 0) - (book.get("available_count") or 0)
    if borrowed > 0:
        return redirect(f"/manage/book/?manager_id={manager_id}&error=대출 중인 책({borrowed}권)이 있어 삭제할 수 없습니다")

    # 삭제
    db.execute("DELETE FROM borrow WHERE isbn = ?", (isbn,))
    db.execute("DELETE FROM book_collection WHERE isbn = ?", (isbn,))
    db.execute("DELETE FROM book_info WHERE isbn = ?", (isbn,))
    db.commit()

    return redirect(f"/manage/book/?manager_id={manager_id}&success=도서가 삭제되었습니다")


@app.route("/user/")
def user_management_page():
    """사용자 관리 웹 페이지 (매니저 전용)"""
    manager_id = request.args.get("manager_id", "")
    error = request.args.get("error", "")
    success = request.args.get("success", "")

    db = get_db()
    manager = None
    users = []

    if manager_id:
        cursor = db.execute("SELECT * FROM user WHERE id = ? AND role = 'MANAGER'", (manager_id,))
        row = cursor.fetchone()
        if row:
            manager = dict(row)
            cursor = db.execute("SELECT * FROM user ORDER BY created_at DESC")
            users = [dict(r) for r in cursor.fetchall()]
        else:
            error = "매니저 권한이 없거나 존재하지 않는 사용자입니다."

    return render_template_string(
        USER_MANAGEMENT_TEMPLATE,
        manager=manager,
        users=users,
        error=error,
        success=success
    )


@app.route("/user/add", methods=["POST"])
def user_add_action():
    """사용자 추가 액션"""
    manager_id = request.args.get("manager_id", "")

    if not manager_id:
        return redirect("/user/?error=매니저 로그인이 필요합니다")

    db = get_db()

    # 매니저 권한 확인
    cursor = db.execute("SELECT role FROM user WHERE id = ?", (manager_id,))
    row = cursor.fetchone()
    if not row or row['role'] != 'MANAGER':
        return redirect("/user/?error=매니저 권한이 없습니다")

    user_id = request.form.get("id", "").strip()
    name = request.form.get("name", "").strip()
    role = request.form.get("role", "USER")

    if not user_id or not name:
        return redirect(f"/user/?manager_id={manager_id}&error=ID와 이름은 필수입니다")

    # 중복 확인
    cursor = db.execute("SELECT id FROM user WHERE id = ?", (user_id,))
    if cursor.fetchone():
        return redirect(f"/user/?manager_id={manager_id}&error=이미 존재하는 ID입니다")

    if role not in ("USER", "MANAGER"):
        role = "USER"

    db.execute(
        "INSERT INTO user (id, name, role) VALUES (?, ?, ?)",
        (user_id, name, role)
    )
    db.commit()

    return redirect(f"/user/?manager_id={manager_id}&success=사용자가 추가되었습니다")


@app.route("/user/delete/<user_id>", methods=["POST"])
def user_delete_action(user_id):
    """사용자 삭제 액션"""
    manager_id = request.args.get("manager_id", "")

    if not manager_id:
        return redirect("/user/?error=매니저 로그인이 필요합니다")

    db = get_db()

    # 매니저 권한 확인
    cursor = db.execute("SELECT role FROM user WHERE id = ?", (manager_id,))
    row = cursor.fetchone()
    if not row or row['role'] != 'MANAGER':
        return redirect("/user/?error=매니저 권한이 없습니다")

    # 자기 자신 삭제 방지
    if user_id == manager_id:
        return redirect(f"/user/?manager_id={manager_id}&error=자기 자신은 삭제할 수 없습니다")

    # 사용자 존재 확인
    cursor = db.execute("SELECT id FROM user WHERE id = ?", (user_id,))
    if cursor.fetchone() is None:
        return redirect(f"/user/?manager_id={manager_id}&error=사용자를 찾을 수 없습니다")

    # 대출 중인 도서 확인
    cursor = db.execute(
        "SELECT COUNT(*) as cnt FROM borrow WHERE user_id = ? AND returned_at IS NULL",
        (user_id,)
    )
    if cursor.fetchone()["cnt"] > 0:
        return redirect(f"/user/?manager_id={manager_id}&error=대출 중인 도서가 있어 삭제할 수 없습니다")

    db.execute("DELETE FROM user WHERE id = ?", (user_id,))
    db.commit()

    return redirect(f"/user/?manager_id={manager_id}&success=사용자가 삭제되었습니다")


# =============================================================================
# API 엔드포인트
# =============================================================================

@app.route("/api/auth/token", methods=["POST"])
def create_auth_token():
    """QR 토큰 생성 (웹 프론트엔드용)"""
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "bad_request", "message": "user_id가 필요합니다"}), 400

    db = get_db()
    cursor = db.execute("SELECT id FROM user WHERE id = ?", (user_id,))
    if cursor.fetchone() is None:
        return jsonify({"error": "not_found", "message": "사용자를 찾을 수 없습니다"}), 404

    token, expires_in = create_token(user_id)
    return jsonify({"token": token, "expires_in": expires_in})


@app.route("/api/book", methods=["GET"])
def list_books():
    """도서 목록 조회"""
    db = get_db()
    cursor = db.execute("""
        SELECT bi.*, bc.total_count, bc.available_count
        FROM book_info bi
        LEFT JOIN book_collection bc ON bi.isbn = bc.isbn
    """)
    books = [dict(row) for row in cursor.fetchall()]
    return jsonify(books)


@app.route("/api/book/<isbn>", methods=["GET"])
def get_book(isbn):
    """도서 상세 조회 (대출자 정보 포함)"""
    db = get_db()
    book = get_book_with_collection(db, isbn)

    if book is None:
        # TODO: 외부 API에서 조회 후 저장
        return jsonify({"error": "not_found", "message": "도서를 찾을 수 없습니다"}), 404

    book['borrowers'] = get_book_borrowers(db, isbn)
    return jsonify(book)


@app.route("/api/book/<isbn>", methods=["PUT"])
def add_book(isbn):
    """도서 추가 (누구나 가능)"""
    data = request.get_json()

    if not data.get("title"):
        return jsonify({"error": "bad_request", "message": "title이 필요합니다"}), 400

    db = get_db()

    # 이미 존재하는지 확인
    existing = get_book_with_collection(db, isbn)
    if existing:
        return jsonify({"error": "conflict", "message": "이미 존재하는 도서입니다"}), 409

    # book_info 추가
    db.execute("""
        INSERT INTO book_info (isbn, title, author, publisher, published_year, language, pages, cover_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        isbn,
        data.get("title"),
        data.get("author"),
        data.get("publisher"),
        data.get("published_year"),
        data.get("language"),
        data.get("pages"),
        data.get("cover_url")
    ))

    # book_collection 추가
    total_count = data.get("total_count", 1)
    db.execute("""
        INSERT INTO book_collection (isbn, total_count, available_count)
        VALUES (?, ?, ?)
    """, (isbn, total_count, total_count))

    db.commit()

    book = get_book_with_collection(db, isbn)
    return jsonify(book), 201


@app.route("/api/borrow/<isbn>", methods=["POST"])
def borrow_book(isbn):
    """도서 대출"""
    data = request.get_json()
    qr_token = data.get("qr_token")

    if not qr_token:
        return jsonify({"error": "bad_request", "message": "qr_token이 필요합니다"}), 400

    # 토큰 검증
    user_id = verify_token(qr_token)
    if user_id is None:
        return jsonify({"error": "unauthorized", "message": "유효하지 않거나 만료된 토큰입니다"}), 401

    db = get_db()

    # 도서 확인
    book = get_book_with_collection(db, isbn)
    if book is None:
        return jsonify({"error": "not_found", "message": "도서를 찾을 수 없습니다"}), 404

    # 재고 확인
    if book.get('available_count', 0) <= 0:
        return jsonify({"error": "no_stock", "message": "대출 가능한 책이 없습니다"}), 400

    # 대출 처리
    db.execute(
        "INSERT INTO borrow (isbn, user_id) VALUES (?, ?)",
        (isbn, user_id)
    )
    db.execute(
        "UPDATE book_collection SET available_count = available_count - 1 WHERE isbn = ?",
        (isbn,)
    )
    db.commit()

    # 업데이트된 정보 조회
    book = get_book_with_collection(db, isbn)

    return jsonify({
        "success": True,
        "message": "대출이 완료되었습니다",
        "book": book
    })


@app.route("/api/return/<isbn>", methods=["POST"])
def return_book(isbn):
    """도서 반납"""
    data = request.get_json()
    qr_token = data.get("qr_token")

    if not qr_token:
        return jsonify({"error": "bad_request", "message": "qr_token이 필요합니다"}), 400

    # 토큰 검증
    user_id = verify_token(qr_token)
    if user_id is None:
        return jsonify({"error": "unauthorized", "message": "유효하지 않거나 만료된 토큰입니다"}), 401

    db = get_db()

    # 대출 기록 확인
    cursor = db.execute(
        "SELECT id FROM borrow WHERE isbn = ? AND user_id = ? AND returned_at IS NULL",
        (isbn, user_id)
    )
    borrow = cursor.fetchone()

    if borrow is None:
        return jsonify({"error": "not_borrowed", "message": "본인이 대출한 기록이 없습니다"}), 400

    # 반납 처리
    db.execute(
        "UPDATE borrow SET returned_at = datetime('now') WHERE id = ?",
        (borrow['id'],)
    )
    db.execute(
        "UPDATE book_collection SET available_count = available_count + 1 WHERE isbn = ?",
        (isbn,)
    )
    db.commit()

    book = get_book_with_collection(db, isbn)

    return jsonify({
        "success": True,
        "message": "반납이 완료되었습니다",
        "book": book
    })


@app.route("/api/user/<user_id>/borrows", methods=["GET"])
def get_user_borrows(user_id):
    """사용자 대출 목록 조회"""
    db = get_db()
    cursor = db.execute(
        "SELECT * FROM borrow WHERE user_id = ? ORDER BY borrowed_at DESC",
        (user_id,)
    )
    records = [dict(row) for row in cursor.fetchall()]
    return jsonify(records)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
