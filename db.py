
import sqlite3, os, datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data.sqlite3")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user' -- 'admin' or 'user'
    );

    CREATE TABLE IF NOT EXISTS items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        name TEXT NOT NULL,
        price REAL NOT NULL DEFAULT 0,
        cost REAL NOT NULL DEFAULT 0,
        qty REAL NOT NULL DEFAULT 0,
        min_qty REAL NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS parties(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL, -- 'customer' or 'supplier'
        name TEXT NOT NULL,
        phone TEXT,
        address TEXT
    );

    CREATE TABLE IF NOT EXISTS invoices(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        number TEXT UNIQUE,
        type TEXT NOT NULL, -- 'sale' or 'purchase'
        party_id INTEGER,
        date TEXT NOT NULL,
        subtotal REAL NOT NULL DEFAULT 0,
        discount REAL NOT NULL DEFAULT 0,
        tax REAL NOT NULL DEFAULT 0,
        total REAL NOT NULL DEFAULT 0,
        user_id INTEGER,
        FOREIGN KEY(party_id) REFERENCES parties(id),
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS invoice_items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        qty REAL NOT NULL DEFAULT 0,
        price REAL NOT NULL DEFAULT 0,
        total REAL NOT NULL DEFAULT 0,
        FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
        FOREIGN KEY(item_id) REFERENCES items(id)
    );
    """)
    conn.commit()

    # Seed admin user if not exists
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users(username, password, role) VALUES (?,?,?)", ("admin","admin","admin"))
        conn.commit()
    conn.close()

def next_invoice_number(prefix):
    conn = get_conn()
    today = datetime.date.today().strftime("%Y%m%d")
    pref = f"{prefix}-{today}-"
    c = conn.cursor()
    c.execute("SELECT number FROM invoices WHERE number LIKE ? ORDER BY number DESC LIMIT 1", (pref+"%",))
    row = c.fetchone()
    if not row:
        return pref + "0001"
    last = int(row['number'].split("-")[-1])
    return f"{pref}{last+1:04d}"
