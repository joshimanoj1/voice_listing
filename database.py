# database.py
import sqlite3
import os

def init_db():
    conn = sqlite3.connect("listings.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            mobile TEXT PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            product_name TEXT,
            product_name_en TEXT,
            material TEXT,
            material_en TEXT,
            description TEXT,
            description_en TEXT,
            price TEXT,
            price_en TEXT,
            tags TEXT,
            tags_en TEXT,
            image_paths TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_mobile) REFERENCES users (mobile)
        )
    """)
    conn.commit()
    conn.close()

def get_user(mobile):
    conn = sqlite3.connect("listings.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE mobile = ?", (mobile,))
    user = c.fetchone()
    conn.close()
    return user

def add_user(mobile, first_name, last_name):
    conn = sqlite3.connect("listings.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (mobile, first_name, last_name) VALUES (?, ?, ?)", 
              (mobile, first_name, last_name))
    conn.commit()
    conn.close()

def get_user_products(user_mobile):
    conn = sqlite3.connect("listings.db")
    c = conn.cursor()
    c.execute("""
        SELECT id, user_mobile, product_name, product_name_en, material, material_en,
               description, description_en, price, price_en, tags, tags_en, image_paths, created_at
        FROM products WHERE user_mobile = ?
    """, (user_mobile,))
    products = c.fetchall()
    conn.close()
    return [
        {
            "id": product[0],
            "user_mobile": product[1],
            "product_name": product[2],
            "product_name_en": product[3],
            "material": product[4],
            "material_en": product[5],
            "description": product[6],
            "description_en": product[7],
            "price": product[8],
            "price_en": product[9],
            "tags": product[10],
            "tags_en": product[11],
            "image_paths": product[12].split(",") if product[12] else [],
            "created_at": product[13]
        }
        for product in products
    ]