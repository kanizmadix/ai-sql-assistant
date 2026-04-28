"""
Creates and populates the SQLite e-commerce database with realistic sample data.

Now seeds 8 tables totalling several thousand rows:
    customers, products, orders, suppliers, employees, reviews,
    categories, addresses

Run once before starting the server:  python sample_data.py
"""

from __future__ import annotations

import random
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "ecommerce.db"

random.seed(42)


# ── Schema -------------------------------------------------------------------

def create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        DROP TABLE IF EXISTS reviews;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS addresses;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS suppliers;
        DROP TABLE IF EXISTS categories;
        DROP TABLE IF EXISTS employees;
        DROP TABLE IF EXISTS customers;

        CREATE TABLE customers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            email       TEXT    NOT NULL UNIQUE,
            city        TEXT    NOT NULL,
            signup_date TEXT    NOT NULL
        );
        CREATE INDEX ix_customers_city ON customers(city);

        CREATE TABLE categories (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL UNIQUE,
            description TEXT
        );

        CREATE TABLE suppliers (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name    TEXT    NOT NULL,
            country TEXT    NOT NULL,
            email   TEXT    NOT NULL UNIQUE,
            rating  REAL    NOT NULL DEFAULT 4.0
        );

        CREATE TABLE employees (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL,
            role       TEXT    NOT NULL,
            email      TEXT    NOT NULL UNIQUE,
            hire_date  TEXT    NOT NULL,
            salary     REAL    NOT NULL,
            manager_id INTEGER REFERENCES employees(id)
        );

        CREATE TABLE products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            category    TEXT    NOT NULL,
            category_id INTEGER REFERENCES categories(id),
            supplier_id INTEGER REFERENCES suppliers(id),
            price       REAL    NOT NULL,
            stock       INTEGER NOT NULL
        );
        CREATE INDEX ix_products_category ON products(category);

        CREATE TABLE addresses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            line1       TEXT    NOT NULL,
            city        TEXT    NOT NULL,
            state       TEXT    NOT NULL,
            postal_code TEXT    NOT NULL,
            country     TEXT    NOT NULL DEFAULT 'USA',
            is_default  INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE orders (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id  INTEGER NOT NULL REFERENCES customers(id),
            product_id   INTEGER NOT NULL REFERENCES products(id),
            employee_id  INTEGER REFERENCES employees(id),
            quantity     INTEGER NOT NULL,
            order_date   TEXT    NOT NULL,
            total        REAL    NOT NULL,
            status       TEXT    NOT NULL DEFAULT 'completed'
        );
        CREATE INDEX ix_orders_customer ON orders(customer_id);
        CREATE INDEX ix_orders_product  ON orders(product_id);
        CREATE INDEX ix_orders_date     ON orders(order_date);

        CREATE TABLE reviews (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            product_id  INTEGER NOT NULL REFERENCES products(id),
            rating      INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
            comment     TEXT,
            created_at  TEXT    NOT NULL
        );
    """)


# ── Seed data ---------------------------------------------------------------

CITIES = [
    ("New York", "NY"), ("Los Angeles", "CA"), ("Chicago", "IL"),
    ("Houston", "TX"), ("Phoenix", "AZ"), ("Philadelphia", "PA"),
    ("San Antonio", "TX"), ("San Diego", "CA"), ("Dallas", "TX"),
    ("San Jose", "CA"), ("Austin", "TX"), ("Jacksonville", "FL"),
    ("San Francisco", "CA"), ("Columbus", "OH"), ("Charlotte", "NC"),
    ("Indianapolis", "IN"), ("Seattle", "WA"), ("Denver", "CO"),
    ("Nashville", "TN"), ("Oklahoma City", "OK"), ("Portland", "OR"),
    ("Boston", "MA"), ("Atlanta", "GA"), ("Miami", "FL"),
]

FIRST_NAMES = [
    "Alice", "Bob", "Carol", "David", "Eva", "Frank", "Grace", "Henry",
    "Iris", "James", "Karen", "Liam", "Mia", "Noah", "Olivia", "Paul",
    "Quinn", "Rachel", "Samuel", "Tina", "Uma", "Victor", "Wendy", "Xavier",
    "Yara", "Zane", "Aaron", "Bella", "Caleb", "Diana", "Ethan", "Fiona",
    "Gabriel", "Hannah", "Ian", "Julia", "Kevin", "Lily", "Mason", "Nora",
]

LAST_NAMES = [
    "Johnson", "Smith", "White", "Brown", "Martinez", "Lee", "Kim", "Wilson",
    "Chen", "Taylor", "Anderson", "Thomas", "Jackson", "Harris", "Martin",
    "Garcia", "Rodriguez", "Lewis", "Clark", "Robinson", "Walker", "Young",
    "Allen", "King", "Wright", "Scott", "Green", "Baker", "Adams", "Nelson",
]


def seed_customers(conn: sqlite3.Connection, n: int = 200) -> list[int]:
    seen_emails = set()
    rows = []
    base = datetime(2022, 1, 1)
    for i in range(n):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"
        email = f"{first.lower()}.{last.lower()}{i}@example.com"
        if email in seen_emails:
            continue
        seen_emails.add(email)
        city, _state = random.choice(CITIES)
        signup = (base + timedelta(days=random.randint(0, 1000))).strftime("%Y-%m-%d")
        rows.append((name, email, city, signup))
    conn.executemany(
        "INSERT INTO customers (name, email, city, signup_date) VALUES (?,?,?,?)",
        rows,
    )
    conn.commit()
    return [r[0] for r in conn.execute("SELECT id FROM customers").fetchall()]


def seed_categories(conn: sqlite3.Connection) -> dict[str, int]:
    cats = [
        ("Electronics", "Consumer electronics and gadgets"),
        ("Apparel", "Clothing, shoes, and accessories"),
        ("Fitness", "Workout and outdoor gear"),
        ("Health", "Wellness and supplements"),
        ("Kitchen", "Cookware and small appliances"),
        ("Home", "Home decor and lighting"),
        ("Stationery", "Office and writing supplies"),
        ("Books", "Print books and audiobooks"),
        ("Toys", "Children's toys and games"),
        ("Garden", "Outdoor and gardening tools"),
    ]
    conn.executemany(
        "INSERT INTO categories (name, description) VALUES (?,?)",
        cats,
    )
    conn.commit()
    return {row[1]: row[0] for row in conn.execute("SELECT id, name FROM categories")}


def seed_suppliers(conn: sqlite3.Connection, n: int = 15) -> list[int]:
    countries = ["USA", "China", "Germany", "Japan", "India", "Vietnam", "Mexico", "Italy"]
    rows = []
    for i in range(n):
        rows.append((
            f"Supplier {chr(65 + (i % 26))}{i}",
            random.choice(countries),
            f"contact{i}@supplier{i}.com",
            round(random.uniform(3.0, 5.0), 2),
        ))
    conn.executemany(
        "INSERT INTO suppliers (name, country, email, rating) VALUES (?,?,?,?)",
        rows,
    )
    conn.commit()
    return [r[0] for r in conn.execute("SELECT id FROM suppliers").fetchall()]


def seed_employees(conn: sqlite3.Connection, n: int = 25) -> list[int]:
    roles = ["Sales Rep", "Account Manager", "Support", "Engineer", "Manager", "Analyst"]
    base = datetime(2018, 1, 1)
    # First seed managers (no manager_id)
    managers = []
    for i in range(3):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        cur = conn.execute(
            "INSERT INTO employees (name, role, email, hire_date, salary, manager_id) VALUES (?,?,?,?,?,?)",
            (
                f"{first} {last}",
                "Manager",
                f"mgr{i}.{last.lower()}@company.com",
                (base + timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d"),
                round(random.uniform(110_000, 160_000), 2),
                None,
            ),
        )
        managers.append(cur.lastrowid)
    for i in range(n - 3):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        conn.execute(
            "INSERT INTO employees (name, role, email, hire_date, salary, manager_id) VALUES (?,?,?,?,?,?)",
            (
                f"{first} {last}",
                random.choice(roles),
                f"emp{i}.{last.lower()}@company.com",
                (base + timedelta(days=random.randint(0, 2000))).strftime("%Y-%m-%d"),
                round(random.uniform(45_000, 120_000), 2),
                random.choice(managers),
            ),
        )
    conn.commit()
    return [r[0] for r in conn.execute("SELECT id FROM employees").fetchall()]


PRODUCT_TEMPLATES = [
    ("Wireless Earbuds",      "Electronics",  89.99),
    ("Mechanical Keyboard",   "Electronics", 149.99),
    ("USB-C Hub",             "Electronics",  49.99),
    ("Smart Watch",           "Electronics", 299.99),
    ("Laptop Stand",          "Electronics",  34.99),
    ("4K Monitor",            "Electronics", 399.99),
    ("Gaming Mouse",          "Electronics",  59.99),
    ("Running Shoes",         "Apparel",      79.99),
    ("Wool Sweater",          "Apparel",      89.99),
    ("Denim Jacket",          "Apparel",     119.99),
    ("Yoga Mat",              "Fitness",      29.99),
    ("Dumbbell Set",          "Fitness",     149.99),
    ("Resistance Bands",      "Fitness",      19.99),
    ("Protein Powder",        "Health",       54.99),
    ("Multivitamin",          "Health",       24.99),
    ("Coffee Maker",          "Kitchen",     119.99),
    ("Blender",               "Kitchen",      79.99),
    ("Water Bottle",          "Kitchen",      24.99),
    ("Desk Lamp",             "Home",         39.99),
    ("Floor Rug",             "Home",        129.99),
    ("Plant Pot Set",         "Home",         19.99),
    ("Notebook Set",          "Stationery",   14.99),
    ("Fountain Pen",          "Stationery",   49.99),
    ("Hardcover Novel",       "Books",        24.99),
    ("Cookbook",              "Books",        29.99),
    ("Lego Set",              "Toys",         59.99),
    ("Board Game",            "Toys",         34.99),
    ("Garden Hose",           "Garden",       39.99),
    ("Pruning Shears",        "Garden",       19.99),
    ("Backpack",              "Apparel",      69.99),
    ("Bluetooth Speaker",     "Electronics", 199.99),
]


def seed_products(
    conn: sqlite3.Connection,
    cat_map: dict[str, int],
    supplier_ids: list[int],
) -> list[tuple[int, float]]:
    rows = []
    for name, cat, price in PRODUCT_TEMPLATES:
        rows.append((
            name,
            cat,
            cat_map.get(cat),
            random.choice(supplier_ids),
            price,
            random.randint(0, 400),
        ))
    conn.executemany(
        """INSERT INTO products (name, category, category_id, supplier_id, price, stock)
           VALUES (?,?,?,?,?,?)""",
        rows,
    )
    conn.commit()
    return [(r[0], r[1]) for r in conn.execute("SELECT id, price FROM products").fetchall()]


def seed_addresses(conn: sqlite3.Connection, customer_ids: list[int]) -> None:
    rows = []
    for cid in customer_ids:
        n_addr = random.randint(1, 2)
        for j in range(n_addr):
            city, state = random.choice(CITIES)
            rows.append((
                cid,
                f"{random.randint(10, 9999)} {random.choice(['Main','Oak','Pine','Maple','Cedar'])} St",
                city,
                state,
                f"{random.randint(10000, 99999)}",
                "USA",
                1 if j == 0 else 0,
            ))
    conn.executemany(
        """INSERT INTO addresses (customer_id, line1, city, state, postal_code, country, is_default)
           VALUES (?,?,?,?,?,?,?)""",
        rows,
    )
    conn.commit()


def seed_orders(
    conn: sqlite3.Connection,
    customer_ids: list[int],
    products: list[tuple[int, float]],
    employee_ids: list[int],
    n: int = 1500,
) -> list[tuple[int, int, int]]:
    statuses = ["completed", "completed", "completed", "shipped", "pending", "cancelled"]
    base = datetime(2023, 1, 1)
    rows = []
    placed: list[tuple[int, int, int]] = []  # (order_id placeholder, customer_id, product_id)
    for _ in range(n):
        cust_id = random.choice(customer_ids)
        prod_id, price = random.choice(products)
        qty = random.randint(1, 5)
        days = random.randint(0, 730)
        order_date = (base + timedelta(days=days)).strftime("%Y-%m-%d")
        total = round(qty * price, 2)
        rows.append((
            cust_id, prod_id, random.choice(employee_ids), qty,
            order_date, total, random.choice(statuses),
        ))
        placed.append((0, cust_id, prod_id))
    conn.executemany(
        """INSERT INTO orders
           (customer_id, product_id, employee_id, quantity, order_date, total, status)
           VALUES (?,?,?,?,?,?,?)""",
        rows,
    )
    conn.commit()
    # Real (customer_id, product_id) pairs available for review seeding
    return [(r[0], r[1], r[2]) for r in conn.execute("SELECT id, customer_id, product_id FROM orders")]


REVIEW_COMMENTS = [
    "Loved it! Exceeded expectations.",
    "Solid product, would recommend.",
    "Average — does the job but nothing special.",
    "Disappointed with the build quality.",
    "Fantastic value for the price.",
    "Arrived quickly and works perfectly.",
    "Not what I expected from the photos.",
    "Five stars all the way.",
    "Great gift, the recipient adored it.",
    "Would buy again without hesitation.",
]


def seed_reviews(
    conn: sqlite3.Connection,
    order_pairs: list[tuple[int, int, int]],
    n: int = 600,
) -> None:
    rows = []
    base = datetime(2023, 2, 1)
    for _ in range(n):
        _oid, cust_id, prod_id = random.choice(order_pairs)
        rating = random.choices([1, 2, 3, 4, 5], weights=[1, 2, 4, 7, 10])[0]
        comment = random.choice(REVIEW_COMMENTS)
        ts = (base + timedelta(days=random.randint(0, 700))).strftime("%Y-%m-%d %H:%M:%S")
        rows.append((cust_id, prod_id, rating, comment, ts))
    conn.executemany(
        """INSERT INTO reviews (customer_id, product_id, rating, comment, created_at)
           VALUES (?,?,?,?,?)""",
        rows,
    )
    conn.commit()


# ── Entrypoint --------------------------------------------------------------

def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    print("Creating tables…")
    create_tables(conn)
    print("Seeding categories…")
    cat_map = seed_categories(conn)
    print("Seeding suppliers…")
    supplier_ids = seed_suppliers(conn)
    print("Seeding employees…")
    employee_ids = seed_employees(conn)
    print("Seeding customers…")
    customer_ids = seed_customers(conn)
    print("Seeding addresses…")
    seed_addresses(conn, customer_ids)
    print("Seeding products…")
    products = seed_products(conn, cat_map, supplier_ids)
    print("Seeding orders…")
    order_pairs = seed_orders(conn, customer_ids, products, employee_ids)
    print("Seeding reviews…")
    seed_reviews(conn, order_pairs)
    conn.close()

    # Print a small summary
    c = sqlite3.connect(DB_PATH)
    print(f"\nDone! Database written to {DB_PATH}")
    for t in ("customers", "categories", "suppliers", "employees", "products", "addresses", "orders", "reviews"):
        n = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:<11}: {n} rows")
    c.close()


if __name__ == "__main__":
    main()
