# -*- coding: utf-8 -*-
"""Модуль подключения к Neon для Android (только pg8000)."""
import os, json, hashlib
import pg8000

DATABASE_URL = os.getenv("DATABASE_URL", "")

def _parse_url(url):
    try:
        rest = url.replace("postgresql://","").replace("postgres://","")
        auth, tail = rest.split("@", 1)
        user, password = auth.split(":", 1)
        host_db = tail.split("/", 1)
        host_port = host_db[0]
        db_part = host_db[1].split("?",1)[0] if len(host_db)>1 else "neondb"
        host, port = (host_port.split(":",1) if ":" in host_port else (host_port,"5432"))
        return user, password, host, db_part, int(port)
    except Exception:
        return None

def get_connection():
    p = _parse_url(DATABASE_URL)
    if p:
        u, pw, h, d, port = p
        return pg8000.connect(user=u, password=pw, host=h, database=d, port=port, ssl_context=True)
    return pg8000.connect(dsn=DATABASE_URL)

def load_users():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users")
        cols = [d[0] for d in cur.description]
        users = {}
        for row in cur.fetchall():
            r = dict(zip(cols, row))
            users[r["username"]] = {
                "username": r["username"], "password_hash": r["password_hash"],
                "full_name": r["full_name"], "role": r["role"],
                "schedule": r["schedule"] or "", "pay_type": r["pay_type"],
                "pay_rate": r["pay_rate"], "language": r["language"],
                "tasks": r["tasks"] if isinstance(r["tasks"], list) else json.loads(r["tasks"] or "[]"),
                "pay_history": r["pay_history"] if isinstance(r["pay_history"], list) else json.loads(r["pay_history"] or "[]"),
            }
        return users
    finally:
        conn.close()

def load_categories():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM categories ORDER BY name")
        cats = cur.fetchall()
        result = {}
        for c in cats:
            cur.execute("SELECT name, price, model FROM products WHERE category_id = %s ORDER BY id", (c[0],))
            result[c[1]] = {"name": c[1], "items": [dict(zip(['name','price','model'], p)) for p in cur.fetchall()]}
        return result
    finally:
        conn.close()

def load_messages(channel=None):
    conn = get_connection()
    try:
        cur = conn.cursor()
        if channel:
            cur.execute("SELECT author, role, text, created_at FROM messages WHERE channel = %s ORDER BY created_at ASC", (channel,))
        else:
            cur.execute("SELECT author, role, text, created_at, channel FROM messages ORDER BY created_at ASC")
        return [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]
    finally:
        conn.close()

def add_message(channel, author, role, text):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO messages (channel, author, role, text) VALUES (%s,%s,%s,%s)", (channel, author, role, text))
        conn.commit()
    finally:
        conn.close()

def hash_password(p):
    return hashlib.pbkdf2_hmac("sha256", p.encode(), b"salt", 100000).hex()

def check_password(p, h):
    return hash_password(p) == h
