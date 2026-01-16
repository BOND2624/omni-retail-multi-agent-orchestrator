-- ShopCore Database Schema
-- Users, Products, Orders

CREATE TABLE IF NOT EXISTS Users (
    UserID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL,
    Email TEXT NOT NULL UNIQUE,
    PremiumStatus BOOLEAN DEFAULT 0
);

CREATE TABLE IF NOT EXISTS Products (
    ProductID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL,
    Category TEXT NOT NULL,
    Price REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS Orders (
    OrderID INTEGER PRIMARY KEY AUTOINCREMENT,
    UserID INTEGER NOT NULL,
    ProductID INTEGER NOT NULL,
    OrderDate TEXT NOT NULL,
    Status TEXT NOT NULL,
    FOREIGN KEY (UserID) REFERENCES Users(UserID),
    FOREIGN KEY (ProductID) REFERENCES Products(ProductID)
);

CREATE INDEX IF NOT EXISTS idx_orders_userid ON Orders(UserID);
CREATE INDEX IF NOT EXISTS idx_orders_productid ON Orders(ProductID);
CREATE INDEX IF NOT EXISTS idx_orders_status ON Orders(Status);
