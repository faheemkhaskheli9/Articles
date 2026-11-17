"""Build the synthetic shop database used by every example.

All names, emails, phone numbers and amounts are generated. Nothing here is
real customer data.
"""
from __future__ import annotations

import random
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit_price_pkr INTEGER NOT NULL
);
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    status TEXT NOT NULL CHECK (status IN ('paid', 'refunded', 'cancelled')),
    total_pkr INTEGER NOT NULL,
    last_update TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL
);
CREATE TABLE staff_salaries (
    id INTEGER PRIMARY KEY,
    staff_name TEXT NOT NULL,
    monthly_salary_pkr INTEGER NOT NULL
);
"""

CITIES = ["Karachi", "Lahore", "Hyderabad", "Islamabad", "Sukkur"]
FIRST = ["Ali", "Sana", "Bilal", "Hira", "Usman", "Ayesha", "Kamran", "Zara", "Imran", "Mehwish"]
LAST = ["Khan", "Shaikh", "Memon", "Qureshi", "Baloch", "Abbasi"]
PRODUCTS = [
    ("Wireless mouse", "electronics", 2500),
    ("USB-C charger", "electronics", 4200),
    ("Cotton kurta", "clothing", 3800),
    ("Lawn suit", "clothing", 6500),
    ("Rice 5kg", "grocery", 1900),
    ("Tea 950g", "grocery", 1650),
]


def build(path: str | Path, seed: int = 7) -> Path:
    """Create (or replace) the sample database at ``path`` and return it."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    rng = random.Random(seed)
    con = sqlite3.connect(path)
    try:
        con.executescript(SCHEMA)
        for cid in range(1, 41):
            name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
            con.execute(
                "INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?)",
                (cid, name, rng.choice(CITIES), f"user{cid}@example.test",
                 f"+92-300-{1000000 + cid:07d}", f"2026-0{rng.randint(1, 9)}-1{rng.randint(0, 9)}"),
            )
        con.executemany("INSERT INTO products VALUES (?, ?, ?, ?)",
                        [(i + 1, *p) for i, p in enumerate(PRODUCTS)])
        item_id = 1
        for oid in range(1, 151):
            status = rng.choices(["paid", "refunded", "cancelled"], weights=[8, 1, 1])[0]
            items = []
            for _ in range(rng.randint(1, 3)):
                pid = rng.randint(1, len(PRODUCTS))
                qty = rng.randint(1, 4)
                items.append((pid, qty))
            total = sum(PRODUCTS[pid - 1][2] * qty for pid, qty in items)
            day = f"2026-{rng.randint(1, 10):02d}-{rng.randint(1, 28):02d}"
            con.execute("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)",
                        (oid, rng.randint(1, 40), status, total, day, day))
            for pid, qty in items:
                con.execute("INSERT INTO order_items VALUES (?, ?, ?, ?)", (item_id, oid, pid, qty))
                item_id += 1
        con.executemany("INSERT INTO staff_salaries VALUES (?, ?, ?)",
                        [(1, "Store manager", 210000), (2, "Analyst", 145000)])
        con.commit()
    finally:
        con.close()
    return path
