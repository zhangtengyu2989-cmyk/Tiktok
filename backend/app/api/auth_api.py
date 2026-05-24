"""
用户认证API - 注册/登录/Token管理
"""
import hashlib
import secrets
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr

router = APIRouter()
security = HTTPBearer()

DB_PATH = "data/tiktok_baseline.db"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天
REFRESH_TOKEN_EXPIRE_DAYS = 30


def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _hash_password(password: str, salt: str = "") -> str:
    if not salt:
        salt = secrets.token_hex(16)
    return hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt.encode(),
        100000
    ).hex() + ":" + salt


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        hash_part, salt = stored_hash.split(":")
        return _hash_password(password, salt) == stored_hash
    except:
        return False


def _generate_token(user_id: str) -> tuple:
    """生成access_token和refresh_token"""
    access_token = secrets.token_urlsafe(32)
    refresh_token = secrets.token_urlsafe(32)
    expires_at = int(time.time()) + ACCESS_TOKEN_EXPIRE_MINUTES * 60

    conn = _get_db()
    conn.execute("""
        INSERT INTO auth_tokens (user_id, access_token, refresh_token, expires_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, access_token, refresh_token, expires_at))
    conn.commit()
    conn.close()

    return access_token, refresh_token, expires_at


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: int
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    created_at: str


@router.post("/auth/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    """用户注册"""
    if len(req.password) < 6:
        raise HTTPException(400, "密码长度至少6位")

    user_id = secrets.token_urlsafe(16)
    password_hash = _hash_password(req.password)

    conn = _get_db()
    try:
        conn.execute("""
            INSERT INTO users (id, username, email, password_hash)
            VALUES (?, ?, ?, ?)
        """, (user_id, req.username, req.email, password_hash))
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        if "username" in str(e):
            raise HTTPException(400, "用户名已存在")
        if "email" in str(e):
            raise HTTPException(400, "邮箱已注册")
        raise HTTPException(400, "注册失败")
    finally:
        conn.close()

    access_token, refresh_token, expires_at = _generate_token(user_id)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
    )


@router.post("/auth/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """用户登录"""
    conn = _get_db()
    try:
        user = conn.execute("""
            SELECT id, username, email, password_hash, is_active
            FROM users
            WHERE username = ? OR email = ?
        """, (req.username, req.username)).fetchone()

        if not user or not _verify_password(req.password, user["password_hash"]):
            raise HTTPException(401, "用户名或密码错误")

        if not user["is_active"]:
            raise HTTPException(403, "账号已被禁用")

        conn.execute("""
            UPDATE users SET last_login_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user["id"],))
        conn.commit()
    finally:
        conn.close()

    access_token, refresh_token, expires_at = _generate_token(user["id"])
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
    )


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshTokenRequest):
    """刷新access_token"""
    conn = _get_db()
    try:
        token_record = conn.execute("""
            SELECT user_id, expires_at FROM auth_tokens
            WHERE refresh_token = ? AND expires_at > ?
        """, (req.refresh_token, int(time.time()))).fetchone()

        if not token_record:
            raise HTTPException(401, "Refresh token无效或已过期")

        # 删除旧token
        conn.execute("DELETE FROM auth_tokens WHERE refresh_token = ?", (req.refresh_token,))
        conn.commit()
    finally:
        conn.close()

    access_token, refresh_token, expires_at = _generate_token(token_record["user_id"])
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
    )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """获取当前用户（依赖注入）"""
    token = credentials.credentials
    conn = _get_db()
    try:
        token_record = conn.execute("""
            SELECT user_id, expires_at FROM auth_tokens
            WHERE access_token = ? AND expires_at > ?
        """, (token, int(time.time()))).fetchone()

        if not token_record:
            raise HTTPException(401, "Token无效或已过期")

        user = conn.execute("""
            SELECT id, username, email, created_at
            FROM users WHERE id = ?
        """, (token_record["user_id"],)).fetchone()

        if not user:
            raise HTTPException(401, "用户不存在")

        return dict(user)
    finally:
        conn.close()


@router.get("/auth/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserResponse(**user)


@router.post("/auth/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """登出"""
    token = credentials.credentials
    conn = _get_db()
    conn.execute("DELETE FROM auth_tokens WHERE access_token = ?", (token,))
    conn.commit()
    conn.close()
    return {"status": "ok"}


def init_auth_tables():
    """初始化认证相关表"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS auth_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            access_token TEXT UNIQUE NOT NULL,
            refresh_token TEXT UNIQUE NOT NULL,
            expires_at INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
