"""
Database initialization and seeding script.
Creates all 4 databases with schemas and deterministic synthetic data.
"""

import sqlite3
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Database paths
DB_DIR = Path(__file__).parent
SQL_DIR = Path(__file__).parent.parent / "sql"

DATABASES = {
    "shopcore": DB_DIR / "shopcore.db",
    "shipstream": DB_DIR / "shipstream.db",
    "payguard": DB_DIR / "payguard.db",
    "caredesk": DB_DIR / "caredesk.db"
}


def init_database(db_name: str, schema_file: str):
    """Initialize a database with its schema."""
    db_path = DATABASES[db_name]
    
    # Remove existing database
    if db_path.exists():
        db_path.unlink()
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Read and execute schema
    schema_path = SQL_DIR / schema_file
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
        cursor.executescript(schema_sql)
    
    conn.commit()
    return conn, cursor


def seed_shopcore():
    """Seed ShopCore database with synthetic data."""
    conn, cursor = init_database("shopcore", "shopcore.sql")
    
    # Users (20 users, some premium)
    users = [
        (1, "Alice Johnson", "alice@example.com", 1),
        (2, "Bob Smith", "bob@example.com", 0),
        (3, "Charlie Brown", "charlie@example.com", 1),
        (4, "Diana Prince", "diana@example.com", 0),
        (5, "Eve Wilson", "eve@example.com", 1),
        (6, "Frank Miller", "frank@example.com", 0),
        (7, "Grace Lee", "grace@example.com", 1),
        (8, "Henry Davis", "henry@example.com", 0),
        (9, "Iris Chen", "iris@example.com", 0),
        (10, "Jack Taylor", "jack@example.com", 1),
        (11, "Karen White", "karen@example.com", 0),
        (12, "Liam O'Brien", "liam@example.com", 1),
        (13, "Mia Garcia", "mia@example.com", 0),
        (14, "Noah Martinez", "noah@example.com", 0),
        (15, "Olivia Anderson", "olivia@example.com", 1),
        (16, "Paul Thompson", "paul@example.com", 0),
        (17, "Quinn Roberts", "quinn@example.com", 1),
        (18, "Rachel Green", "rachel@example.com", 0),
        (19, "Steve Martin", "steve@example.com", 0),
        (20, "Tina Turner", "tina@example.com", 1),
    ]
    
    cursor.executemany(
        "INSERT INTO Users (UserID, Name, Email, PremiumStatus) VALUES (?, ?, ?, ?)",
        users
    )
    
    # Products (30 products)
    products = [
        (1, "Gaming Monitor", "Electronics", 299.99),
        (2, "Wireless Headphones", "Electronics", 149.99),
        (3, "Mechanical Keyboard", "Electronics", 89.99),
        (4, "Gaming Mouse", "Electronics", 59.99),
        (5, "USB-C Cable", "Accessories", 19.99),
        (6, "Laptop Stand", "Accessories", 49.99),
        (7, "Webcam HD", "Electronics", 79.99),
        (8, "Desk Lamp", "Furniture", 39.99),
        (9, "Office Chair", "Furniture", 199.99),
        (10, "Monitor Stand", "Accessories", 29.99),
        (11, "USB Hub", "Accessories", 24.99),
        (12, "Wireless Charger", "Accessories", 34.99),
        (13, "Bluetooth Speaker", "Electronics", 69.99),
        (14, "Tablet Stand", "Accessories", 19.99),
        (15, "Cable Organizer", "Accessories", 14.99),
        (16, "Desk Mat", "Accessories", 24.99),
        (17, "Monitor Light Bar", "Accessories", 59.99),
        (18, "Laptop Sleeve", "Accessories", 29.99),
        (19, "Phone Stand", "Accessories", 12.99),
        (20, "Power Bank", "Electronics", 44.99),
        (21, "Smart Watch", "Electronics", 199.99),
        (22, "Fitness Tracker", "Electronics", 79.99),
        (23, "Earbuds", "Electronics", 99.99),
        (24, "Noise Cancelling Headphones", "Electronics", 249.99),
        (25, "Microphone", "Electronics", 129.99),
        (26, "Ring Light", "Accessories", 49.99),
        (27, "Green Screen", "Accessories", 39.99),
        (28, "Tripod", "Accessories", 34.99),
        (29, "SD Card 128GB", "Accessories", 19.99),
        (30, "External SSD 1TB", "Electronics", 89.99),
    ]
    
    cursor.executemany(
        "INSERT INTO Products (ProductID, Name, Category, Price) VALUES (?, ?, ?, ?)",
        products
    )
    
    # Orders (40 orders, some from last week)
    base_date = datetime.now()
    orders = [
        (1, 1, 1, (base_date - timedelta(days=7)).strftime("%Y-%m-%d"), "Delivered"),  # Gaming Monitor
        (2, 2, 2, (base_date - timedelta(days=10)).strftime("%Y-%m-%d"), "Delivered"),  # Headphones
        (3, 3, 1, (base_date - timedelta(days=5)).strftime("%Y-%m-%d"), "In Transit"),  # Gaming Monitor
        (4, 4, 2, (base_date - timedelta(days=8)).strftime("%Y-%m-%d"), "Returned"),  # Headphones
        (5, 5, 3, (base_date - timedelta(days=3)).strftime("%Y-%m-%d"), "Processing"),
        (6, 1, 4, (base_date - timedelta(days=6)).strftime("%Y-%m-%d"), "In Transit"),
        (7, 6, 5, (base_date - timedelta(days=12)).strftime("%Y-%m-%d"), "Delivered"),
        (8, 7, 1, (base_date - timedelta(days=4)).strftime("%Y-%m-%d"), "In Transit"),
        (9, 8, 6, (base_date - timedelta(days=9)).strftime("%Y-%m-%d"), "Delivered"),
        (10, 9, 7, (base_date - timedelta(days=2)).strftime("%Y-%m-%d"), "Processing"),
        (11, 10, 8, (base_date - timedelta(days=11)).strftime("%Y-%m-%d"), "Delivered"),
        (12, 11, 9, (base_date - timedelta(days=7)).strftime("%Y-%m-%d"), "In Transit"),
        (13, 12, 10, (base_date - timedelta(days=13)).strftime("%Y-%m-%d"), "Delivered"),
        (14, 13, 11, (base_date - timedelta(days=1)).strftime("%Y-%m-%d"), "Processing"),
        (15, 14, 12, (base_date - timedelta(days=14)).strftime("%Y-%m-%d"), "Delivered"),
        (16, 15, 13, (base_date - timedelta(days=6)).strftime("%Y-%m-%d"), "In Transit"),
        (17, 16, 14, (base_date - timedelta(days=8)).strftime("%Y-%m-%d"), "Delivered"),
        (18, 17, 15, (base_date - timedelta(days=4)).strftime("%Y-%m-%d"), "Processing"),
        (19, 18, 16, (base_date - timedelta(days=10)).strftime("%Y-%m-%d"), "Delivered"),
        (20, 19, 17, (base_date - timedelta(days=5)).strftime("%Y-%m-%d"), "In Transit"),
        (21, 20, 18, (base_date - timedelta(days=7)).strftime("%Y-%m-%d"), "Delivered"),
        (22, 1, 19, (base_date - timedelta(days=3)).strftime("%Y-%m-%d"), "Processing"),
        (23, 2, 20, (base_date - timedelta(days=9)).strftime("%Y-%m-%d"), "Delivered"),
        (24, 3, 21, (base_date - timedelta(days=6)).strftime("%Y-%m-%d"), "In Transit"),
        (25, 4, 22, (base_date - timedelta(days=11)).strftime("%Y-%m-%d"), "Delivered"),
        (26, 5, 23, (base_date - timedelta(days=2)).strftime("%Y-%m-%d"), "Processing"),
        (27, 6, 24, (base_date - timedelta(days=8)).strftime("%Y-%m-%d"), "Delivered"),
        (28, 7, 25, (base_date - timedelta(days=4)).strftime("%Y-%m-%d"), "In Transit"),
        (29, 8, 26, (base_date - timedelta(days=12)).strftime("%Y-%m-%d"), "Delivered"),
        (30, 9, 27, (base_date - timedelta(days=1)).strftime("%Y-%m-%d"), "Processing"),
        (31, 10, 28, (base_date - timedelta(days=7)).strftime("%Y-%m-%d"), "In Transit"),
        (32, 11, 29, (base_date - timedelta(days=5)).strftime("%Y-%m-%d"), "Delivered"),
        (33, 12, 30, (base_date - timedelta(days=9)).strftime("%Y-%m-%d"), "Delivered"),
        (34, 13, 1, (base_date - timedelta(days=3)).strftime("%Y-%m-%d"), "Processing"),
        (35, 14, 2, (base_date - timedelta(days=6)).strftime("%Y-%m-%d"), "In Transit"),
        (36, 15, 3, (base_date - timedelta(days=10)).strftime("%Y-%m-%d"), "Delivered"),
        (37, 16, 4, (base_date - timedelta(days=2)).strftime("%Y-%m-%d"), "Processing"),
        (38, 17, 5, (base_date - timedelta(days=8)).strftime("%Y-%m-%d"), "Delivered"),
        (39, 18, 6, (base_date - timedelta(days=4)).strftime("%Y-%m-%d"), "In Transit"),
        (40, 19, 7, (base_date - timedelta(days=7)).strftime("%Y-%m-%d"), "Delivered"),
    ]
    
    cursor.executemany(
        "INSERT INTO Orders (OrderID, UserID, ProductID, OrderDate, Status) VALUES (?, ?, ?, ?, ?)",
        orders
    )
    
    conn.commit()
    conn.close()
    print(f"[OK] Seeded ShopCore database: {len(users)} users, {len(products)} products, {len(orders)} orders")


def seed_shipstream():
    """Seed ShipStream database with synthetic data."""
    conn, cursor = init_database("shipstream", "shipstream.sql")
    
    # Warehouses (5 warehouses)
    warehouses = [
        (1, "New York Warehouse", "John Manager"),
        (2, "Los Angeles Warehouse", "Sarah Manager"),
        (3, "Chicago Warehouse", "Mike Manager"),
        (4, "Houston Warehouse", "Lisa Manager"),
        (5, "Phoenix Warehouse", "Tom Manager"),
    ]
    
    cursor.executemany(
        "INSERT INTO Warehouses (WarehouseID, Location, ManagerName) VALUES (?, ?, ?)",
        warehouses
    )
    
    # Get order statuses from ShopCore database for consistency
    shopcore_path = DATABASES["shopcore"]
    if shopcore_path.exists():
        import sqlite3 as sqlite3_shopcore
        shopcore_conn = sqlite3_shopcore.connect(str(shopcore_path))
        shopcore_cursor = shopcore_conn.cursor()
        shopcore_cursor.execute("SELECT OrderID, Status FROM Orders")
        order_status_map = {row[0]: row[1] for row in shopcore_cursor.fetchall()}
        shopcore_conn.close()
    else:
        # Fallback: use default statuses if ShopCore DB doesn't exist yet
        order_status_map = {}
    
    # Shipments (35 shipments for various orders)
    # Create a mapping from OrderID to Order Status for consistency
    
    base_date = datetime.now()
    shipments = []
    
    # Generate shipments with consistent status and dates
    for order_id in range(1, 36):  # Orders 1-35
        order_status = order_status_map.get(order_id, "In Transit")
        tracking_num = f"TRK{order_id:03d}"
        
        # Set EstimatedArrival based on status:
        # - Delivered: arrival date in the past (3-7 days ago)
        # - In Transit: arrival date in the future (1-5 days)
        # - Processing: arrival date in the future (3-7 days)
        # - Returned: arrival date in the past (5-10 days ago)
        if order_status == "Delivered":
            est_arrival = (base_date - timedelta(days=3 + (order_id % 5))).strftime("%Y-%m-%d")
            shipment_status = "Delivered"
        elif order_status == "In Transit":
            est_arrival = (base_date + timedelta(days=1 + (order_id % 4))).strftime("%Y-%m-%d")
            shipment_status = "In Transit"
        elif order_status == "Processing":
            est_arrival = (base_date + timedelta(days=3 + (order_id % 4))).strftime("%Y-%m-%d")
            shipment_status = "Preparing"  # More appropriate for processing orders
        elif order_status == "Returned":
            est_arrival = (base_date - timedelta(days=5 + (order_id % 5))).strftime("%Y-%m-%d")
            shipment_status = "Returned"
        else:
            est_arrival = (base_date + timedelta(days=2)).strftime("%Y-%m-%d")
            shipment_status = "In Transit"
        
        shipments.append((order_id, order_id, tracking_num, est_arrival, shipment_status))
    
    cursor.executemany(
        "INSERT INTO Shipments (ShipmentID, OrderID, TrackingNumber, EstimatedArrival, Status) VALUES (?, ?, ?, ?, ?)",
        shipments
    )
    
    # TrackingEvents (50 events)
    events = [
        (1, 1, 1, (base_date - timedelta(days=6)).strftime("%Y-%m-%d %H:%M:%S"), "Package picked up"),
        (2, 1, 1, (base_date - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S"), "In transit to warehouse"),
        (3, 1, 1, (base_date - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"), "Arrived at warehouse"),
        (4, 1, 1, (base_date - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"), "Out for delivery"),
        (5, 2, 2, (base_date - timedelta(days=9)).strftime("%Y-%m-%d %H:%M:%S"), "Package picked up"),
        (6, 2, 2, (base_date - timedelta(days=8)).strftime("%Y-%m-%d %H:%M:%S"), "Delivered"),
        (7, 3, 1, (base_date - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"), "Package picked up"),
        (8, 3, 1, (base_date - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"), "In transit"),
        (9, 3, 2, (base_date - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"), "Arrived at warehouse"),
        (10, 4, 3, (base_date - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S"), "Package picked up"),
        (11, 4, 3, (base_date - timedelta(days=6)).strftime("%Y-%m-%d %H:%M:%S"), "Returned to sender"),
        (12, 5, 4, (base_date - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"), "Package picked up"),
        (13, 6, 1, (base_date - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S"), "Package picked up"),
        (14, 6, 1, (base_date - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"), "In transit"),
        (15, 7, 2, (base_date - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"), "Package picked up"),
        (16, 7, 2, (base_date - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"), "In transit"),
        (17, 8, 5, (base_date - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"), "Delivered"),
        (18, 9, 1, (base_date - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"), "Package picked up"),
        (19, 10, 2, (base_date - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"), "Package picked up"),
        (20, 11, 3, (base_date - timedelta(days=0)).strftime("%Y-%m-%d %H:%M:%S"), "Package picked up"),
        (21, 12, 1, (base_date - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"), "Package picked up"),
        (22, 13, 2, (base_date - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"), "Delivered"),
        (23, 14, 4, (base_date - timedelta(days=0)).strftime("%Y-%m-%d %H:%M:%S"), "Package picked up"),
        (24, 15, 1, (base_date - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S"), "Package picked up"),
        (25, 15, 1, (base_date - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"), "In transit"),
        (26, 16, 5, (base_date - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"), "Delivered"),
        (27, 17, 1, (base_date - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"), "Package picked up"),
        (28, 18, 2, (base_date - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"), "Package picked up"),
        (29, 19, 3, (base_date - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"), "Delivered"),
        (30, 20, 1, (base_date - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"), "Package picked up"),
        (31, 20, 1, (base_date - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"), "In transit"),
        (32, 21, 2, (base_date - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"), "Delivered"),
        (33, 22, 4, (base_date - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"), "Package picked up"),
        (34, 23, 5, (base_date - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"), "Delivered"),
        (35, 24, 1, (base_date - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S"), "Package picked up"),
        (36, 24, 1, (base_date - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"), "In transit"),
        (37, 25, 2, (base_date - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"), "Delivered"),
        (38, 26, 3, (base_date - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"), "Package picked up"),
        (39, 27, 4, (base_date - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"), "Delivered"),
        (40, 28, 1, (base_date - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"), "Package picked up"),
        (41, 28, 1, (base_date - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"), "In transit"),
        (42, 29, 5, (base_date - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"), "Delivered"),
        (43, 30, 1, (base_date - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"), "Package picked up"),
        (44, 31, 2, (base_date - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"), "Package picked up"),
        (45, 31, 2, (base_date - timedelta(days=0)).strftime("%Y-%m-%d %H:%M:%S"), "In transit"),
        (46, 32, 3, (base_date - timedelta(days=0)).strftime("%Y-%m-%d %H:%M:%S"), "Delivered"),
        (47, 33, 4, (base_date - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"), "Delivered"),
        (48, 34, 1, (base_date - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"), "Package picked up"),
        (49, 35, 2, (base_date - timedelta(days=0)).strftime("%Y-%m-%d %H:%M:%S"), "Package picked up"),
        (50, 35, 2, (base_date - timedelta(days=0)).strftime("%Y-%m-%d %H:%M:%S"), "In transit"),
    ]
    
    cursor.executemany(
        "INSERT INTO TrackingEvents (EventID, ShipmentID, WarehouseID, Timestamp, StatusUpdate) VALUES (?, ?, ?, ?, ?)",
        events
    )
    
    conn.commit()
    conn.close()
    print(f"[OK] Seeded ShipStream database: {len(warehouses)} warehouses, {len(shipments)} shipments, {len(events)} tracking events")


def seed_payguard():
    """Seed PayGuard database with synthetic data."""
    conn, cursor = init_database("payguard", "payguard.sql")
    
    # Wallets (20 wallets, one per user)
    wallets = [
        (1, 1, 500.00, "USD"),
        (2, 2, 250.00, "USD"),
        (3, 3, 750.00, "USD"),
        (4, 4, 100.00, "USD"),
        (5, 5, 1000.00, "USD"),
        (6, 6, 300.00, "USD"),
        (7, 7, 600.00, "USD"),
        (8, 8, 150.00, "USD"),
        (9, 9, 400.00, "USD"),
        (10, 10, 800.00, "USD"),
        (11, 11, 200.00, "USD"),
        (12, 12, 550.00, "USD"),
        (13, 13, 350.00, "USD"),
        (14, 14, 450.00, "USD"),
        (15, 15, 900.00, "USD"),
        (16, 16, 180.00, "USD"),
        (17, 17, 650.00, "USD"),
        (18, 18, 220.00, "USD"),
        (19, 19, 380.00, "USD"),
        (20, 20, 720.00, "USD"),
    ]
    
    cursor.executemany(
        "INSERT INTO Wallets (WalletID, UserID, Balance, Currency) VALUES (?, ?, ?, ?)",
        wallets
    )
    
    # Transactions (45 transactions)
    base_date = datetime.now()
    transactions = [
        (1, 1, 1, 299.99, "Purchase", (base_date - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")),
        (2, 2, 2, 149.99, "Purchase", (base_date - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")),
        (3, 3, 3, 299.99, "Purchase", (base_date - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")),
        (4, 4, 4, 149.99, "Purchase", (base_date - timedelta(days=8)).strftime("%Y-%m-%d %H:%M:%S")),
        (5, 4, 4, 149.99, "Refund", (base_date - timedelta(days=6)).strftime("%Y-%m-%d %H:%M:%S")),
        (6, 5, 5, 89.99, "Purchase", (base_date - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")),
        (7, 6, 6, 59.99, "Purchase", (base_date - timedelta(days=6)).strftime("%Y-%m-%d %H:%M:%S")),
        (8, 7, 7, 299.99, "Purchase", (base_date - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S")),
        (9, 8, 8, 199.99, "Purchase", (base_date - timedelta(days=9)).strftime("%Y-%m-%d %H:%M:%S")),
        (10, 9, 9, 79.99, "Purchase", (base_date - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")),
        (11, 10, 10, 29.99, "Purchase", (base_date - timedelta(days=11)).strftime("%Y-%m-%d %H:%M:%S")),
        (12, 11, 11, 199.99, "Purchase", (base_date - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")),
        (13, 12, 12, 49.99, "Purchase", (base_date - timedelta(days=13)).strftime("%Y-%m-%d %H:%M:%S")),
        (14, 13, 13, 24.99, "Purchase", (base_date - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")),
        (15, 14, 14, 34.99, "Purchase", (base_date - timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S")),
        (16, 15, 15, 69.99, "Purchase", (base_date - timedelta(days=6)).strftime("%Y-%m-%d %H:%M:%S")),
        (17, 16, 16, 19.99, "Purchase", (base_date - timedelta(days=8)).strftime("%Y-%m-%d %H:%M:%S")),
        (18, 17, 17, 24.99, "Purchase", (base_date - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S")),
        (19, 18, 18, 59.99, "Purchase", (base_date - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")),
        (20, 19, 19, 29.99, "Purchase", (base_date - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")),
        (21, 20, 20, 12.99, "Purchase", (base_date - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")),
        (22, 1, 21, 44.99, "Purchase", (base_date - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")),
        (23, 2, 22, 199.99, "Purchase", (base_date - timedelta(days=9)).strftime("%Y-%m-%d %H:%M:%S")),
        (24, 3, 23, 79.99, "Purchase", (base_date - timedelta(days=6)).strftime("%Y-%m-%d %H:%M:%S")),
        (25, 4, 24, 99.99, "Purchase", (base_date - timedelta(days=11)).strftime("%Y-%m-%d %H:%M:%S")),
        (26, 5, 25, 129.99, "Purchase", (base_date - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")),
        (27, 6, 26, 49.99, "Purchase", (base_date - timedelta(days=8)).strftime("%Y-%m-%d %H:%M:%S")),
        (28, 7, 27, 39.99, "Purchase", (base_date - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S")),
        (29, 8, 28, 34.99, "Purchase", (base_date - timedelta(days=12)).strftime("%Y-%m-%d %H:%M:%S")),
        (30, 9, 29, 19.99, "Purchase", (base_date - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")),
        (31, 10, 30, 89.99, "Purchase", (base_date - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")),
        (32, 11, 1, 299.99, "Purchase", (base_date - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")),
        (33, 12, 2, 149.99, "Purchase", (base_date - timedelta(days=9)).strftime("%Y-%m-%d %H:%M:%S")),
        (34, 13, 3, 89.99, "Purchase", (base_date - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")),
        (35, 14, 4, 59.99, "Purchase", (base_date - timedelta(days=6)).strftime("%Y-%m-%d %H:%M:%S")),
        (36, 15, 5, 19.99, "Purchase", (base_date - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")),
        (37, 16, 6, 49.99, "Purchase", (base_date - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")),
        (38, 17, 7, 79.99, "Purchase", (base_date - timedelta(days=8)).strftime("%Y-%m-%d %H:%M:%S")),
        (39, 18, 8, 39.99, "Purchase", (base_date - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S")),
        (40, 19, 9, 199.99, "Purchase", (base_date - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")),
        (41, 20, 10, 29.99, "Purchase", (base_date - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")),
        (42, 1, 11, 24.99, "Purchase", (base_date - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")),
        (43, 2, 12, 34.99, "Purchase", (base_date - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")),
        (44, 3, 13, 69.99, "Purchase", (base_date - timedelta(days=6)).strftime("%Y-%m-%d %H:%M:%S")),
        (45, 4, 14, 19.99, "Purchase", (base_date - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")),
    ]
    
    cursor.executemany(
        "INSERT INTO Transactions (TransactionID, WalletID, OrderID, Amount, Type, Timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        transactions
    )
    
    # PaymentMethods (25 payment methods)
    payment_methods = [
        (1, 1, "Credit Card", "2025-12-31"),
        (2, 2, "Debit Card", "2025-11-30"),
        (3, 3, "PayPal", None),
        (4, 4, "Credit Card", "2025-10-31"),
        (5, 5, "Bank Transfer", None),
        (6, 6, "Credit Card", "2026-01-31"),
        (7, 7, "PayPal", None),
        (8, 8, "Debit Card", "2025-09-30"),
        (9, 9, "Credit Card", "2025-12-31"),
        (10, 10, "PayPal", None),
        (11, 11, "Credit Card", "2026-02-28"),
        (12, 12, "Bank Transfer", None),
        (13, 13, "Debit Card", "2025-11-30"),
        (14, 14, "Credit Card", "2025-12-31"),
        (15, 15, "PayPal", None),
        (16, 16, "Credit Card", "2026-01-31"),
        (17, 17, "Debit Card", "2025-10-31"),
        (18, 18, "PayPal", None),
        (19, 19, "Credit Card", "2025-12-31"),
        (20, 20, "Bank Transfer", None),
        (21, 1, "PayPal", None),
        (22, 2, "Credit Card", "2026-03-31"),
        (23, 3, "Debit Card", "2025-11-30"),
        (24, 4, "PayPal", None),
        (25, 5, "Credit Card", "2025-12-31"),
    ]
    
    cursor.executemany(
        "INSERT INTO PaymentMethods (MethodID, WalletID, Provider, ExpiryDate) VALUES (?, ?, ?, ?)",
        payment_methods
    )
    
    conn.commit()
    conn.close()
    print(f"[OK] Seeded PayGuard database: {len(wallets)} wallets, {len(transactions)} transactions, {len(payment_methods)} payment methods")


def seed_caredesk():
    """Seed CareDesk database with synthetic data."""
    conn, cursor = init_database("caredesk", "caredesk.sql")
    
    # Tickets (30 tickets)
    base_date = datetime.now()
    tickets = [
        (1, 1, 1, "Delivery Issue", "Open", (base_date - timedelta(days=1)).strftime("%Y-%m-%d")),
        (2, 2, 2, "Product Quality", "Closed", (base_date - timedelta(days=15)).strftime("%Y-%m-%d")),
        (3, 3, 3, "Delivery Issue", "Open", (base_date - timedelta(days=3)).strftime("%Y-%m-%d")),
        (4, 4, 4, "Refund Request", "Closed", (base_date - timedelta(days=8)).strftime("%Y-%m-%d")),
        (5, 5, 5, "Payment Issue", "Open", (base_date - timedelta(days=2)).strftime("%Y-%m-%d")),
        (6, 6, 6, "Delivery Issue", "Open", (base_date - timedelta(days=4)).strftime("%Y-%m-%d")),
        (7, 7, 7, "Product Quality", "Closed", (base_date - timedelta(days=12)).strftime("%Y-%m-%d")),
        (8, 8, 8, "Refund Request", "Closed", (base_date - timedelta(days=10)).strftime("%Y-%m-%d")),
        (9, 9, 9, "Delivery Issue", "Open", (base_date - timedelta(days=1)).strftime("%Y-%m-%d")),
        (10, 10, 10, "Payment Issue", "Open", (base_date - timedelta(days=5)).strftime("%Y-%m-%d")),
        (11, 11, 11, "Product Quality", "Closed", (base_date - timedelta(days=7)).strftime("%Y-%m-%d")),
        (12, 12, 12, "Delivery Issue", "Open", (base_date - timedelta(days=2)).strftime("%Y-%m-%d")),
        (13, 13, 13, "Refund Request", "Closed", (base_date - timedelta(days=14)).strftime("%Y-%m-%d")),
        (14, 14, 14, "Payment Issue", "Open", (base_date - timedelta(days=1)).strftime("%Y-%m-%d")),
        (15, 15, 15, "Delivery Issue", "Open", (base_date - timedelta(days=3)).strftime("%Y-%m-%d")),
        (16, 16, 16, "Product Quality", "Closed", (base_date - timedelta(days=9)).strftime("%Y-%m-%d")),
        (17, 17, 17, "Refund Request", "Closed", (base_date - timedelta(days=6)).strftime("%Y-%m-%d")),
        (18, 18, 18, "Delivery Issue", "Open", (base_date - timedelta(days=2)).strftime("%Y-%m-%d")),
        (19, 19, 19, "Payment Issue", "Open", (base_date - timedelta(days=4)).strftime("%Y-%m-%d")),
        (20, 20, 20, "Product Quality", "Closed", (base_date - timedelta(days=11)).strftime("%Y-%m-%d")),
        (21, 1, 21, "Delivery Issue", "Open", (base_date - timedelta(days=1)).strftime("%Y-%m-%d")),
        (22, 2, 22, "Refund Request", "Closed", (base_date - timedelta(days=13)).strftime("%Y-%m-%d")),
        (23, 3, 23, "Payment Issue", "Open", (base_date - timedelta(days=2)).strftime("%Y-%m-%d")),
        (24, 4, 24, "Product Quality", "Closed", (base_date - timedelta(days=8)).strftime("%Y-%m-%d")),
        (25, 5, 25, "Delivery Issue", "Open", (base_date - timedelta(days=1)).strftime("%Y-%m-%d")),
        (26, 6, 26, "Refund Request", "Closed", (base_date - timedelta(days=7)).strftime("%Y-%m-%d")),
        (27, 7, 27, "Payment Issue", "Open", (base_date - timedelta(days=3)).strftime("%Y-%m-%d")),
        (28, 8, 28, "Product Quality", "Closed", (base_date - timedelta(days=10)).strftime("%Y-%m-%d")),
        (29, 9, 29, "Delivery Issue", "Open", (base_date - timedelta(days=1)).strftime("%Y-%m-%d")),
        (30, 10, 30, "Refund Request", "Closed", (base_date - timedelta(days=5)).strftime("%Y-%m-%d")),
    ]
    
    cursor.executemany(
        "INSERT INTO Tickets (TicketID, UserID, ReferenceID, IssueType, Status, CreatedDate) VALUES (?, ?, ?, ?, ?, ?)",
        tickets
    )
    
    # TicketMessages (60 messages)
    messages = [
        (1, 1, "Customer", "My package hasn't arrived yet", (base_date - timedelta(days=1, hours=10)).strftime("%Y-%m-%d %H:%M:%S")),
        (2, 1, "Support", "We're looking into this for you", (base_date - timedelta(days=1, hours=11)).strftime("%Y-%m-%d %H:%M:%S")),
        (3, 2, "Customer", "The product quality is poor", (base_date - timedelta(days=15, hours=9)).strftime("%Y-%m-%d %H:%M:%S")),
        (4, 2, "Support", "We apologize for the inconvenience", (base_date - timedelta(days=15, hours=10)).strftime("%Y-%m-%d %H:%M:%S")),
        (5, 3, "Customer", "Where is my order?", (base_date - timedelta(days=3, hours=14)).strftime("%Y-%m-%d %H:%M:%S")),
        (6, 3, "Support", "Checking tracking information", (base_date - timedelta(days=3, hours=15)).strftime("%Y-%m-%d %H:%M:%S")),
        (7, 4, "Customer", "I want a refund", (base_date - timedelta(days=8, hours=12)).strftime("%Y-%m-%d %H:%M:%S")),
        (8, 4, "Support", "Refund processed", (base_date - timedelta(days=8, hours=13)).strftime("%Y-%m-%d %H:%M:%S")),
        (9, 5, "Customer", "Payment didn't go through", (base_date - timedelta(days=2, hours=16)).strftime("%Y-%m-%d %H:%M:%S")),
        (10, 5, "Support", "Investigating payment issue", (base_date - timedelta(days=2, hours=17)).strftime("%Y-%m-%d %H:%M:%S")),
        (11, 6, "Customer", "Package delayed", (base_date - timedelta(days=4, hours=10)).strftime("%Y-%m-%d %H:%M:%S")),
        (12, 6, "Support", "We'll update you soon", (base_date - timedelta(days=4, hours=11)).strftime("%Y-%m-%d %H:%M:%S")),
        (13, 7, "Customer", "Product damaged", (base_date - timedelta(days=12, hours=9)).strftime("%Y-%m-%d %H:%M:%S")),
        (14, 7, "Support", "Replacement sent", (base_date - timedelta(days=12, hours=10)).strftime("%Y-%m-%d %H:%M:%S")),
        (15, 8, "Customer", "Refund request", (base_date - timedelta(days=10, hours=14)).strftime("%Y-%m-%d %H:%M:%S")),
        (16, 8, "Support", "Processing refund", (base_date - timedelta(days=10, hours=15)).strftime("%Y-%m-%d %H:%M:%S")),
        (17, 9, "Customer", "Order not received", (base_date - timedelta(days=1, hours=11)).strftime("%Y-%m-%d %H:%M:%S")),
        (18, 9, "Support", "Checking status", (base_date - timedelta(days=1, hours=12)).strftime("%Y-%m-%d %H:%M:%S")),
        (19, 10, "Customer", "Payment failed", (base_date - timedelta(days=5, hours=13)).strftime("%Y-%m-%d %H:%M:%S")),
        (20, 10, "Support", "Looking into it", (base_date - timedelta(days=5, hours=14)).strftime("%Y-%m-%d %H:%M:%S")),
        (21, 11, "Customer", "Quality issue", (base_date - timedelta(days=7, hours=10)).strftime("%Y-%m-%d %H:%M:%S")),
        (22, 11, "Support", "We'll resolve this", (base_date - timedelta(days=7, hours=11)).strftime("%Y-%m-%d %H:%M:%S")),
        (23, 12, "Customer", "Delivery problem", (base_date - timedelta(days=2, hours=15)).strftime("%Y-%m-%d %H:%M:%S")),
        (24, 12, "Support", "Investigating", (base_date - timedelta(days=2, hours=16)).strftime("%Y-%m-%d %H:%M:%S")),
        (25, 13, "Customer", "Need refund", (base_date - timedelta(days=14, hours=9)).strftime("%Y-%m-%d %H:%M:%S")),
        (26, 13, "Support", "Refund approved", (base_date - timedelta(days=14, hours=10)).strftime("%Y-%m-%d %H:%M:%S")),
        (27, 14, "Customer", "Payment error", (base_date - timedelta(days=1, hours=12)).strftime("%Y-%m-%d %H:%M:%S")),
        (28, 14, "Support", "Checking payment", (base_date - timedelta(days=1, hours=13)).strftime("%Y-%m-%d %H:%M:%S")),
        (29, 15, "Customer", "Where's my package?", (base_date - timedelta(days=3, hours=11)).strftime("%Y-%m-%d %H:%M:%S")),
        (30, 15, "Support", "Tracking your order", (base_date - timedelta(days=3, hours=12)).strftime("%Y-%m-%d %H:%M:%S")),
        (31, 16, "Customer", "Product defect", (base_date - timedelta(days=9, hours=14)).strftime("%Y-%m-%d %H:%M:%S")),
        (32, 16, "Support", "Replacement ordered", (base_date - timedelta(days=9, hours=15)).strftime("%Y-%m-%d %H:%M:%S")),
        (33, 17, "Customer", "Refund needed", (base_date - timedelta(days=6, hours=10)).strftime("%Y-%m-%d %H:%M:%S")),
        (34, 17, "Support", "Processing", (base_date - timedelta(days=6, hours=11)).strftime("%Y-%m-%d %H:%M:%S")),
        (35, 18, "Customer", "Delivery delayed", (base_date - timedelta(days=2, hours=13)).strftime("%Y-%m-%d %H:%M:%S")),
        (36, 18, "Support", "We'll update you", (base_date - timedelta(days=2, hours=14)).strftime("%Y-%m-%d %H:%M:%S")),
        (37, 19, "Customer", "Payment issue", (base_date - timedelta(days=4, hours=15)).strftime("%Y-%m-%d %H:%M:%S")),
        (38, 19, "Support", "Investigating", (base_date - timedelta(days=4, hours=16)).strftime("%Y-%m-%d %H:%M:%S")),
        (39, 20, "Customer", "Quality problem", (base_date - timedelta(days=11, hours=9)).strftime("%Y-%m-%d %H:%M:%S")),
        (40, 20, "Support", "We'll fix this", (base_date - timedelta(days=11, hours=10)).strftime("%Y-%m-%d %H:%M:%S")),
        (41, 21, "Customer", "Package missing", (base_date - timedelta(days=1, hours=10)).strftime("%Y-%m-%d %H:%M:%S")),
        (42, 21, "Support", "Checking tracking", (base_date - timedelta(days=1, hours=11)).strftime("%Y-%m-%d %H:%M:%S")),
        (43, 22, "Customer", "Refund request", (base_date - timedelta(days=13, hours=12)).strftime("%Y-%m-%d %H:%M:%S")),
        (44, 22, "Support", "Refund processed", (base_date - timedelta(days=13, hours=13)).strftime("%Y-%m-%d %H:%M:%S")),
        (45, 23, "Customer", "Payment failed", (base_date - timedelta(days=2, hours=14)).strftime("%Y-%m-%d %H:%M:%S")),
        (46, 23, "Support", "Looking into payment", (base_date - timedelta(days=2, hours=15)).strftime("%Y-%m-%d %H:%M:%S")),
        (47, 24, "Customer", "Product issue", (base_date - timedelta(days=8, hours=11)).strftime("%Y-%m-%d %H:%M:%S")),
        (48, 24, "Support", "Replacement sent", (base_date - timedelta(days=8, hours=12)).strftime("%Y-%m-%d %H:%M:%S")),
        (49, 25, "Customer", "Order not here", (base_date - timedelta(days=1, hours=9)).strftime("%Y-%m-%d %H:%M:%S")),
        (50, 25, "Support", "Checking delivery", (base_date - timedelta(days=1, hours=10)).strftime("%Y-%m-%d %H:%M:%S")),
        (51, 26, "Customer", "Need refund", (base_date - timedelta(days=7, hours=13)).strftime("%Y-%m-%d %H:%M:%S")),
        (52, 26, "Support", "Refund approved", (base_date - timedelta(days=7, hours=14)).strftime("%Y-%m-%d %H:%M:%S")),
        (53, 27, "Customer", "Payment problem", (base_date - timedelta(days=3, hours=15)).strftime("%Y-%m-%d %H:%M:%S")),
        (54, 27, "Support", "Investigating", (base_date - timedelta(days=3, hours=16)).strftime("%Y-%m-%d %H:%M:%S")),
        (55, 28, "Customer", "Quality concern", (base_date - timedelta(days=10, hours=10)).strftime("%Y-%m-%d %H:%M:%S")),
        (56, 28, "Support", "We'll resolve", (base_date - timedelta(days=10, hours=11)).strftime("%Y-%m-%d %H:%M:%S")),
        (57, 29, "Customer", "Delivery issue", (base_date - timedelta(days=1, hours=12)).strftime("%Y-%m-%d %H:%M:%S")),
        (58, 29, "Support", "Checking status", (base_date - timedelta(days=1, hours=13)).strftime("%Y-%m-%d %H:%M:%S")),
        (59, 30, "Customer", "Refund needed", (base_date - timedelta(days=5, hours=14)).strftime("%Y-%m-%d %H:%M:%S")),
        (60, 30, "Support", "Processing refund", (base_date - timedelta(days=5, hours=15)).strftime("%Y-%m-%d %H:%M:%S")),
    ]
    
    cursor.executemany(
        "INSERT INTO TicketMessages (MessageID, TicketID, Sender, Content, Timestamp) VALUES (?, ?, ?, ?, ?)",
        messages
    )
    
    # SatisfactionSurveys (20 surveys)
    surveys = [
        (1, 2, 4, "Good service"),
        (2, 4, 5, "Excellent refund process"),
        (3, 7, 3, "Could be better"),
        (4, 8, 4, "Satisfied"),
        (5, 11, 5, "Great support"),
        (6, 13, 4, "Quick resolution"),
        (7, 16, 3, "Average"),
        (8, 17, 5, "Very helpful"),
        (9, 20, 4, "Good experience"),
        (10, 22, 5, "Excellent service"),
        (11, 24, 3, "Okay"),
        (12, 26, 4, "Satisfied"),
        (13, 28, 5, "Outstanding"),
        (14, 30, 4, "Good"),
        (15, 1, 2, "Still waiting"),
        (16, 3, 3, "In progress"),
        (17, 5, 2, "Not resolved"),
        (18, 6, 3, "Working on it"),
        (19, 9, 2, "Pending"),
        (20, 12, 3, "Ongoing"),
    ]
    
    cursor.executemany(
        "INSERT INTO SatisfactionSurveys (SurveyID, TicketID, Rating, Comments) VALUES (?, ?, ?, ?)",
        surveys
    )
    
    conn.commit()
    conn.close()
    print(f"[OK] Seeded CareDesk database: {len(tickets)} tickets, {len(messages)} messages, {len(surveys)} surveys")


def main():
    """Initialize and seed all databases."""
    print("Initializing databases...")
    print("=" * 50)
    
    seed_shopcore()
    seed_shipstream()
    seed_payguard()
    seed_caredesk()
    
    print("=" * 50)
    print("[OK] All databases initialized and seeded successfully!")
    
    # Validate databases
    print("\nValidating databases...")
    for db_name, db_path in DATABASES.items():
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"  {db_name}: {len(tables)} tables")
        conn.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
