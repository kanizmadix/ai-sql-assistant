"""
Creates and populates the SQLite e-commerce database with realistic sample data.
Run this once before starting the server: python sample_data.py
"""

import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "ecommerce.db"


def create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS customers;

        CREATE TABLE customers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            email       TEXT    NOT NULL UNIQUE,
            city        TEXT    NOT NULL,
            signup_date TEXT    NOT NULL
        );

        CREATE TABLE products (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT    NOT NULL,
            category TEXT    NOT NULL,
            price    REAL    NOT NULL,
            stock    INTEGER NOT NULL
        );

        CREATE TABLE orders (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            product_id  INTEGER NOT NULL REFERENCES products(id),
            quantity    INTEGER NOT NULL,
            order_date  TEXT    NOT NULL,
            total       REAL    NOT NULL
        );
    """)


def seed_customers(conn: sqlite3.Connection) -> list[int]:
    customers = [
        ("Alice Johnson",    "alice@example.com",    "New York",      "2022-03-15"),
        ("Bob Smith",        "bob@example.com",      "Los Angeles",   "2022-05-22"),
        ("Carol White",      "carol@example.com",    "Chicago",       "2022-07-08"),
        ("David Brown",      "david@example.com",    "Houston",       "2022-09-14"),
        ("Eva Martinez",     "eva@example.com",      "Phoenix",       "2022-11-01"),
        ("Frank Lee",        "frank@example.com",    "Philadelphia",  "2023-01-20"),
        ("Grace Kim",        "grace@example.com",    "San Antonio",   "2023-03-05"),
        ("Henry Wilson",     "henry@example.com",    "San Diego",     "2023-04-18"),
        ("Iris Chen",        "iris@example.com",     "Dallas",        "2023-06-09"),
        ("James Taylor",     "james@example.com",    "San Jose",      "2023-07-25"),
        ("Karen Anderson",   "karen@example.com",    "Austin",        "2023-08-30"),
        ("Liam Thomas",      "liam@example.com",     "Jacksonville",  "2023-09-12"),
        ("Mia Jackson",      "mia@example.com",      "San Francisco", "2023-10-07"),
        ("Noah Harris",      "noah@example.com",     "Columbus",      "2023-11-19"),
        ("Olivia Martin",    "olivia@example.com",   "Charlotte",     "2023-12-03"),
        ("Paul Garcia",      "paul@example.com",     "Indianapolis",  "2024-01-14"),
        ("Quinn Rodriguez",  "quinn@example.com",    "Seattle",       "2024-02-28"),
        ("Rachel Lewis",     "rachel@example.com",   "Denver",        "2024-03-22"),
        ("Samuel Clark",     "samuel@example.com",   "Nashville",     "2024-04-10"),
        ("Tina Robinson",    "tina@example.com",     "Oklahoma City", "2024-05-05"),
    ]
    cursor = conn.executemany(
        "INSERT INTO customers (name, email, city, signup_date) VALUES (?,?,?,?)",
        customers,
    )
    conn.commit()
    return list(range(1, len(customers) + 1))


def seed_products(conn: sqlite3.Connection) -> list[tuple[int, float]]:
    products = [
        ("Wireless Earbuds",       "Electronics",  89.99,  120),
        ("Mechanical Keyboard",    "Electronics", 149.99,   45),
        ("USB-C Hub",              "Electronics",  49.99,  200),
        ("Smart Watch",            "Electronics", 299.99,   30),
        ("Laptop Stand",           "Electronics",  34.99,  175),
        ("Running Shoes",          "Apparel",       79.99,   90),
        ("Yoga Mat",               "Fitness",       29.99,  150),
        ("Protein Powder",         "Health",        54.99,   80),
        ("Coffee Maker",           "Kitchen",      119.99,   60),
        ("Water Bottle",           "Kitchen",       24.99,  300),
        ("Desk Lamp",              "Home",          39.99,  110),
        ("Notebook Set",           "Stationery",    14.99,  400),
        ("Backpack",               "Apparel",       69.99,   70),
        ("Bluetooth Speaker",      "Electronics", 199.99,   55),
        ("Plant Pot Set",          "Home",          19.99,  220),
    ]
    cursor = conn.executemany(
        "INSERT INTO products (name, category, price, stock) VALUES (?,?,?,?)",
        products,
    )
    conn.commit()
    # Return list of (product_id, price) tuples
    rows = conn.execute("SELECT id, price FROM products").fetchall()
    return [(r[0], r[1]) for r in rows]


def seed_orders(
    conn: sqlite3.Connection,
    customer_ids: list[int],
    products: list[tuple[int, float]],
) -> None:
    random.seed(42)
    orders = []
    base_date = datetime(2023, 1, 1)

    for _ in range(50):
        cust_id = random.choice(customer_ids)
        prod_id, price = random.choice(products)
        qty = random.randint(1, 5)
        days_offset = random.randint(0, 500)
        order_date = (base_date + timedelta(days=days_offset)).strftime("%Y-%m-%d")
        total = round(qty * price, 2)
        orders.append((cust_id, prod_id, qty, order_date, total))

    conn.executemany(
        "INSERT INTO orders (customer_id, product_id, quantity, order_date, total) VALUES (?,?,?,?,?)",
        orders,
    )
    conn.commit()


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    print("Creating tables…")
    create_tables(conn)
    print("Seeding customers…")
    customer_ids = seed_customers(conn)
    print("Seeding products…")
    products = seed_products(conn)
    print("Seeding orders…")
    seed_orders(conn, customer_ids, products)
    conn.close()
    print(f"Done! Database written to {DB_PATH}")
    print(f"  customers : {len(customer_ids)} rows")
    print(f"  products  : {len(products)} rows")
    print(f"  orders    : 50 rows")


if __name__ == "__main__":
    main()
