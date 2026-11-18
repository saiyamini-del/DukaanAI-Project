"""
database.py - SQLite Database persistence layer for Dukaan AI (English Edition).
Handles customers, transactions, business settings, and balance calculations.
"""

import sqlite3
import os
from datetime import datetime, date, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dukaan_ai.db")

def get_connection():
    """Establish and return SQLite connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables with indexes and default settings."""
    conn = get_connection()
    cursor = conn.cursor()

    # Customers table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT UNIQUE,
        address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Transactions table
    # type: 'GIVEN' (Credit to customer - shopkeeper will receive money)
    #       'RECEIVED' (Payment received from customer - debt settled)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        type TEXT NOT NULL CHECK(type IN ('GIVEN', 'RECEIVED')),
        note TEXT,
        date DATE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
    );
    """)

    # Business settings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS business_settings (
        id INTEGER PRIMARY KEY,
        shop_name TEXT NOT NULL DEFAULT 'Sri Lakshmi Supermarket & General Store',
        owner_name TEXT NOT NULL DEFAULT 'Ramesh Babu',
        phone TEXT NOT NULL DEFAULT '9876543210',
        upi_id TEXT NOT NULL DEFAULT 'dukaan@upi',
        currency_symbol TEXT NOT NULL DEFAULT '₹',
        language TEXT NOT NULL DEFAULT 'English'
    );
    """)

    # Ensure default settings row exists
    cursor.execute("SELECT COUNT(*) FROM business_settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO business_settings (id, shop_name, owner_name, phone, upi_id, currency_symbol, language)
        VALUES (1, 'Sri Lakshmi Supermarket & General Store', 'Ramesh Babu', '9876543210', 'dukaan@upi', '₹', 'English')
        """)
    else:
        cursor.execute("""
        UPDATE business_settings 
        SET shop_name = 'Sri Lakshmi Supermarket & General Store',
            owner_name = 'Ramesh Babu',
            language = 'English'
        WHERE id = 1 AND (shop_name LIKE '%శ్రీ%' OR owner_name LIKE '%రమేష్%')
        """)

    conn.commit()
    conn.close()

# ----------------- Customer CRUD ----------------- #

def get_customers(search_query=None):
    """Fetch all customers with calculated net pending balances."""
    conn = get_connection()
    cursor = conn.cursor()

    base_query = """
    SELECT 
        c.id, 
        c.name, 
        c.phone, 
        c.address,
        c.created_at,
        COALESCE(SUM(CASE WHEN t.type = 'GIVEN' THEN t.amount ELSE 0 END), 0) AS total_given,
        COALESCE(SUM(CASE WHEN t.type = 'RECEIVED' THEN t.amount ELSE 0 END), 0) AS total_received,
        (COALESCE(SUM(CASE WHEN t.type = 'GIVEN' THEN t.amount ELSE 0 END), 0) - 
         COALESCE(SUM(CASE WHEN t.type = 'RECEIVED' THEN t.amount ELSE 0 END), 0)) AS net_balance
    FROM customers c
    LEFT JOIN transactions t ON c.id = t.customer_id
    """

    params = []
    if search_query:
        base_query += " WHERE c.name LIKE ? OR c.phone LIKE ?"
        params.extend([f"%{search_query}%", f"%{search_query}%"])

    base_query += " GROUP BY c.id ORDER BY net_balance DESC, c.name ASC"

    cursor.execute(base_query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_customer_by_id(customer_id):
    """Fetch a single customer by id with net balance."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
        c.id, 
        c.name, 
        c.phone, 
        c.address,
        c.created_at,
        COALESCE(SUM(CASE WHEN t.type = 'GIVEN' THEN t.amount ELSE 0 END), 0) AS total_given,
        COALESCE(SUM(CASE WHEN t.type = 'RECEIVED' THEN t.amount ELSE 0 END), 0) AS total_received,
        (COALESCE(SUM(CASE WHEN t.type = 'GIVEN' THEN t.amount ELSE 0 END), 0) - 
         COALESCE(SUM(CASE WHEN t.type = 'RECEIVED' THEN t.amount ELSE 0 END), 0)) AS net_balance
    FROM customers c
    LEFT JOIN transactions t ON c.id = t.customer_id
    WHERE c.id = ?
    GROUP BY c.id
    """, (customer_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def find_or_create_customer(name, phone=None):
    """Find customer by name or create a new one automatically."""
    conn = get_connection()
    cursor = conn.cursor()
    cleaned_name = name.strip()

    cursor.execute("SELECT id, name FROM customers WHERE LOWER(name) = LOWER(?)", (cleaned_name,))
    row = cursor.fetchone()
    if row:
        conn.close()
        return row["id"], row["name"], False

    # Create new customer
    cursor.execute("INSERT INTO customers (name, phone) VALUES (?, ?)", (cleaned_name, phone))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id, cleaned_name, True

def add_customer(name, phone=None, address=None):
    """Add a new customer."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)", 
                       (name.strip(), phone.strip() if phone else None, address.strip() if address else None))
        conn.commit()
        customer_id = cursor.lastrowid
        conn.close()
        return customer_id, None
    except sqlite3.IntegrityError:
        conn.close()
        return None, "Customer with this phone number already exists."

# ----------------- Transactions CRUD ----------------- #

def add_transaction(customer_id, amount, trans_type, note=None, trans_date=None):
    """Add a new ledger transaction."""
    if not trans_date:
        trans_date = date.today().isoformat()
    elif isinstance(trans_date, date):
        trans_date = trans_date.isoformat()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO transactions (customer_id, amount, type, note, date)
    VALUES (?, ?, ?, ?, ?)
    """, (customer_id, float(amount), trans_type, note.strip() if note else "", trans_date))
    conn.commit()
    trans_id = cursor.lastrowid
    conn.close()
    return trans_id

def get_transactions(customer_id=None, trans_type=None, start_date=None, end_date=None, limit=None):
    """Fetch transactions with optional filters."""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT 
        t.id,
        t.customer_id,
        c.name AS customer_name,
        c.phone AS customer_phone,
        t.amount,
        t.type,
        t.note,
        t.date,
        t.created_at
    FROM transactions t
    JOIN customers c ON t.customer_id = c.id
    WHERE 1=1
    """
    params = []

    if customer_id:
        query += " AND t.customer_id = ?"
        params.append(customer_id)
    if trans_type and trans_type != "ALL":
        query += " AND t.type = ?"
        params.append(trans_type)
    if start_date:
        query += " AND t.date >= ?"
        params.append(str(start_date))
    if end_date:
        query += " AND t.date <= ?"
        params.append(str(end_date))

    query += " ORDER BY t.date DESC, t.id DESC"

    if limit:
        query += f" LIMIT {int(limit)}"

    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def delete_transaction(trans_id):
    """Delete a transaction by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ?", (trans_id,))
    conn.commit()
    conn.close()

# ----------------- Dashboard & Analytics ----------------- #

def get_dashboard_kpis():
    """Calculate key financial metrics for the shopkeeper."""
    conn = get_connection()
    cursor = conn.cursor()

    today_str = date.today().isoformat()

    # Overall Total Given (Credit to collect) & Received
    cursor.execute("""
    SELECT 
        COALESCE(SUM(CASE WHEN type = 'GIVEN' THEN amount ELSE 0 END), 0) AS total_given,
        COALESCE(SUM(CASE WHEN type = 'RECEIVED' THEN amount ELSE 0 END), 0) AS total_received
    FROM transactions
    """)
    totals = cursor.fetchone()
    total_given = totals["total_given"]
    total_received = totals["total_received"]
    total_dues_to_collect = max(0, total_given - total_received)

    # Today's Received (Cash collected today)
    cursor.execute("""
    SELECT COALESCE(SUM(amount), 0) FROM transactions 
    WHERE type = 'RECEIVED' AND date = ?
    """, (today_str,))
    today_collected = cursor.fetchone()[0]

    # Today's Given (Credit given today)
    cursor.execute("""
    SELECT COALESCE(SUM(amount), 0) FROM transactions 
    WHERE type = 'GIVEN' AND date = ?
    """, (today_str,))
    today_credit_given = cursor.fetchone()[0]

    # Count of active customers with pending dues
    cursor.execute("""
    SELECT COUNT(*) FROM (
        SELECT customer_id,
               SUM(CASE WHEN type = 'GIVEN' THEN amount ELSE -amount END) AS balance
        FROM transactions
        GROUP BY customer_id
        HAVING balance > 0
    )
    """)
    active_debtors = cursor.fetchone()[0]

    # Total customers count
    cursor.execute("SELECT COUNT(*) FROM customers")
    total_customers = cursor.fetchone()[0]

    # Today transaction count
    cursor.execute("SELECT COUNT(*) FROM transactions WHERE date = ?", (today_str,))
    today_tx_count = cursor.fetchone()[0]

    conn.close()

    return {
        "total_dues_to_collect": total_dues_to_collect,
        "today_collected": today_collected,
        "today_credit_given": today_credit_given,
        "active_debtors": active_debtors,
        "total_customers": total_customers,
        "today_tx_count": today_tx_count,
        "total_lifetime_credit": total_given,
        "total_lifetime_collected": total_received
    }

def get_settings():
    """Get business profile settings."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM business_settings WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}

def update_settings(shop_name, owner_name, phone, upi_id):
    """Update business settings."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE business_settings 
    SET shop_name = ?, owner_name = ?, phone = ?, upi_id = ?
    WHERE id = 1
    """, (shop_name, owner_name, phone, upi_id))
    conn.commit()
    conn.close()

# ----------------- Sample Data Seeder (English) ----------------- #

def seed_sample_data():
    """Seed realistic retail store demo data in English."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # Clear existing
    cursor.execute("DELETE FROM transactions")
    cursor.execute("DELETE FROM customers")

    sample_customers = [
        ("Ramesh Kumar", "9848012345", "Gandhi Road, Near Park"),
        ("Suresh Varma", "9848023456", "Main Bazaar, 2nd Cross"),
        ("Venkat Rao", "9848034567", "Teachers Colony, Plot 14"),
        ("Lakshmi Devi", "9848045678", "Station Road, Apartment 3B"),
        ("Rahul Sharma", "9848056789", "Commercial Complex, Shop 12"),
        ("Pooja Patel", "9848067890", "Green Valley Enclave, House 8")
    ]

    cursor.executemany("INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)", sample_customers)
    conn.commit()

    # Fetch customer IDs
    cursor.execute("SELECT id, name FROM customers")
    cust_map = {row["name"]: row["id"] for row in cursor.fetchall()}

    today = date.today()
    c_ramesh = cust_map["Ramesh Kumar"]
    c_suresh = cust_map["Suresh Varma"]
    c_venkat = cust_map["Venkat Rao"]
    c_lakshmi = cust_map["Lakshmi Devi"]
    c_rahul = cust_map["Rahul Sharma"]
    c_pooja = cust_map["Pooja Patel"]

    transactions = [
        # Today
        (c_ramesh, 450.0, 'GIVEN', 'Rice 5kg & Toor Dal', (today - timedelta(days=0)).isoformat()),
        (c_suresh, 300.0, 'RECEIVED', 'Cash repayment towards balance', (today - timedelta(days=0)).isoformat()),
        (c_venkat, 220.0, 'GIVEN', 'Refined Sunflower Oil (1 Liter)', (today - timedelta(days=0)).isoformat()),
        (c_lakshmi, 150.0, 'RECEIVED', 'UPI Payment via GPay', (today - timedelta(days=0)).isoformat()),
        
        # Yesterday
        (c_ramesh, 200.0, 'RECEIVED', 'Partial cash settlement', (today - timedelta(days=1)).isoformat()),
        (c_rahul, 680.0, 'GIVEN', 'Wheat Flour 5kg, Sugar & Tea Powder', (today - timedelta(days=1)).isoformat()),
        (c_pooja, 120.0, 'GIVEN', 'Bathing Soaps & Toothpaste', (today - timedelta(days=1)).isoformat()),

        # 3 days ago
        (c_suresh, 550.0, 'GIVEN', 'Weekly Kirana Provisions', (today - timedelta(days=3)).isoformat()),
        (c_venkat, 400.0, 'GIVEN', 'Pure Ghee & Basmati Rice', (today - timedelta(days=3)).isoformat()),
        (c_lakshmi, 380.0, 'GIVEN', 'Spices, Dry Fruits & Masala', (today - timedelta(days=4)).isoformat()),

        # Past week
        (c_pooja, 500.0, 'RECEIVED', 'Complete balance cleared', (today - timedelta(days=7)).isoformat()),
        (c_rahul, 200.0, 'RECEIVED', 'PhonePe QR Payment', (today - timedelta(days=8)).isoformat()),
        (c_ramesh, 850.0, 'GIVEN', 'Monthly Grocery Basket', (today - timedelta(days=10)).isoformat()),
    ]

    cursor.executemany("""
    INSERT INTO transactions (customer_id, amount, type, note, date)
    VALUES (?, ?, ?, ?, ?)
    """, transactions)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    seed_sample_data()
    print("Database seeded with English data successfully!")
