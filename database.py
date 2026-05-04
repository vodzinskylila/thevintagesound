# database.py
# Banco de dados SQLite — salvo em "data/vintage_sound.db"
# SQLite já vem instalado com o Python, não precisa instalar nada extra.

import sqlite3
import os
import uuid
import bcrypt
from datetime import datetime

DB_DIR  = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DB_DIR, "vintage_sound.db")


def get_conn():
    """Retorna uma conexão com o banco. Cada request usa a sua própria."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # resultados como dicionário
    conn.execute("PRAGMA journal_mode=WAL") # melhor performance de escrita
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ─── Criação das tabelas ───────────────────────────────────────────────────────
def init_db():
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          TEXT PRIMARY KEY,
            first_name  TEXT NOT NULL,
            last_name   TEXT NOT NULL,
            email       TEXT NOT NULL UNIQUE,
            password    TEXT NOT NULL,
            role        TEXT NOT NULL DEFAULT 'customer',
            newsletter  INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS products (
            id           TEXT PRIMARY KEY,
            slug         TEXT NOT NULL UNIQUE,
            title        TEXT NOT NULL,
            artist       TEXT NOT NULL,
            genre        TEXT NOT NULL,
            year         INTEGER,
            label        TEXT,
            pressing     TEXT,
            description  TEXT,
            price        REAL NOT NULL,
            stock        INTEGER NOT NULL DEFAULT 0,
            image_url    TEXT,
            tags         TEXT DEFAULT '[]',
            featured     INTEGER DEFAULT 0,
            created_at   TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS cart_items (
            id          TEXT PRIMARY KEY,
            user_id     TEXT NOT NULL,
            product_id  TEXT NOT NULL,
            quantity    INTEGER NOT NULL DEFAULT 1,
            added_at    TEXT NOT NULL,
            FOREIGN KEY (user_id)    REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS orders (
            id               TEXT PRIMARY KEY,
            order_number     TEXT NOT NULL UNIQUE,
            user_id          TEXT NOT NULL,
            items            TEXT NOT NULL,
            shipping_address TEXT NOT NULL,
            payment_method   TEXT NOT NULL,
            subtotal         REAL NOT NULL,
            shipping         REAL NOT NULL,
            total            REAL NOT NULL,
            status           TEXT NOT NULL DEFAULT 'pending',
            status_history   TEXT NOT NULL DEFAULT '[]',
            created_at       TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS subscriptions (
            id               TEXT PRIMARY KEY,
            user_id          TEXT NOT NULL,
            plan_id          TEXT NOT NULL,
            plan_name        TEXT NOT NULL,
            price            REAL NOT NULL,
            interval_type    TEXT NOT NULL,
            status           TEXT NOT NULL DEFAULT 'active',
            payment_method   TEXT NOT NULL,
            start_date       TEXT NOT NULL,
            next_billing     TEXT NOT NULL,
            cancelled_at     TEXT,
            created_at       TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """)
    print("  → Tabelas criadas/verificadas.")


# ─── Seed de dados iniciais ────────────────────────────────────────────────────
SUBSCRIPTION_PLANS = [
    {
        "id": "collectors-circle",
        "name": "Collector's Circle",
        "description": "1 disco curado por mês + exclusivos para membros",
        "price": 149.90,
        "interval": "monthly",
        "perks": [
            "1 disco curado mensalmente",
            "Acesso antecipado a lançamentos limitados",
            "20% de desconto em todos os produtos",
            "Frete grátis em todos os pedidos",
            "Newsletter exclusiva Needle Drop",
        ],
    },
    {
        "id": "audiophile-club",
        "name": "Audiophile Club",
        "description": "2 discos premium por mês + materiais de leitura",
        "price": 249.90,
        "interval": "monthly",
        "perks": [
            "2 discos premium mensalmente",
            "Acesso antecipado a lançamentos limitados",
            "30% de desconto em todos os produtos",
            "Frete grátis em todos os pedidos",
            "Newsletter exclusiva Needle Drop",
            "Acesso ao arquivo digital da revista",
        ],
    },
]

SEED_PRODUCTS = [
    ("dark-side-of-the-moon", "The Dark Side of the Moon", "Pink Floyd",       "Rock",   1973, "Harvest Records",   "Prensagem Audiófila 180g",       "Remasterização 2023. A obra-prima definitiva do rock progressivo.", 248.00, 12, "https://imgs.search.brave.com/0E2txGz-yYIf-sF0ytgcF4k-SH7j1vNJqOgdXyyG-rc/rs:fit:860:0:0:0/g:ce/aHR0cHM6Ly9pbWFn/ZXMtbmEuc3NsLWlt/YWdlcy1hbWF6b24u/Y29tL2ltYWdlcy9J/LzYxMFJHSmxHMVpM/LmpwZw", '["audiophile","classic","rock"]', 1),
    ("chega-de-saudade",       "Chega de Saudade",         "João Gilberto",    "MPB",    1959, "Odeon",             "Edição Exclusiva 180g Blue Marble","O álbum que deu origem à Bossa Nova.",                             299.00,  5, "https://i.pinimg.com/1200x/ef/ff/10/efff109238afd85cfa24fac55a8fb994.jpg",                                                                    '["bossa nova","mpb","classic","limited"]', 1),
    ("kind-of-blue",           "Kind of Blue",             "Miles Davis",      "Jazz",   1959, "Columbia Records",  "Mono Reissue 180g",               "O álbum de jazz mais vendido de todos os tempos.",                 242.00,  8, "https://upload.wikimedia.org/wikipedia/en/f/f9/Miles_Davis_%E2%80%93_Kind_of_Blue.jpg",                                                        '["jazz","classic","audiophile"]', 0),
    ("thriller",               "Thriller",                 "Michael Jackson",  "Soul",   1982, "Epic Records",      "Picture Disc Edição Limitada",    "O álbum mais vendido da história em picture disc colorido.",       349.00,  3, "https://upload.wikimedia.org/wikipedia/en/5/55/Michael_Jackson_-_Thriller.png",                                                                '["pop","soul","limited","picture-disc"]', 1),
    ("illmatic",               "Illmatic",                 "Nas",              "Hip-hop",1994, "Columbia Records",  "Anniversary Edition 180g",        "Clássico absoluto do hip-hop. Prensagem comemorativa de 30 anos.", 189.00, 15, "https://upload.wikimedia.org/wikipedia/en/2/2e/Nas_Illmatic.jpg",                                                                             '["hip-hop","classic","anniversary"]', 0),
    ("rumours",                "Rumours",                  "Fleetwood Mac",    "Rock",   1977, "Warner Bros.",      "Super Deluxe 45rpm 2LP",          "Masterizado em 45rpm para máxima fidelidade sonora. Duplo LP.",    145.00, 20, "https://upload.wikimedia.org/wikipedia/en/f/f9/Rumours.png",                                                                                  '["rock","classic","45rpm"]', 0),
    ("whats-going-on",         "What's Going On",          "Marvin Gaye",      "Soul",   1971, "Tamla / Motown",   "Motown Reissue 180g",             "Obra-prima social e musical do soul americano.",                   155.00, 10, "https://upload.wikimedia.org/wikipedia/en/1/1f/MarvinGayeWhat%27sGoingOnalbumcover.jpg",                                                       '["soul","classic","motown"]', 0),
    ("ready-to-die",           "Ready to Die",             "The Notorious B.I.G.", "Hip-hop",1994,"Bad Boy Records","Clear Vinyl 180g",               "O debut lendário do Biggie em vinil transparente de colecionador.",139.00,  7, "https://upload.wikimedia.org/wikipedia/en/4/45/Ready_to_Die.jpg",                                                                            '["hip-hop","limited","clear-vinyl"]', 0),
]


def seed_database():
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        # Produtos
        existing = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if existing == 0:
            for p in SEED_PRODUCTS:
                conn.execute(
                    """INSERT INTO products
                       (id,slug,title,artist,genre,year,label,pressing,description,
                        price,stock,image_url,tags,featured,created_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (str(uuid.uuid4()), *p, now),
                )
            print("  → Produtos inseridos.")

        # Admin
        admin = conn.execute("SELECT id FROM users WHERE email=?", ("admin@vintagesound.com",)).fetchone()
        if not admin:
            hashed = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
            conn.execute(
                "INSERT INTO users (id,first_name,last_name,email,password,role,newsletter,created_at) VALUES (?,?,?,?,?,?,?,?)",
                (str(uuid.uuid4()), "Admin", "Vintage", "admin@vintagesound.com", hashed, "admin", 1, now),
            )
            print("  → Usuário admin criado.")

    print("✅  Banco de dados pronto. Arquivo: data/vintage_sound.db")
