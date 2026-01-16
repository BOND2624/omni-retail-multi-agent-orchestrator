-- PayGuard Database Schema
-- Wallets, Transactions, PaymentMethods

CREATE TABLE IF NOT EXISTS Wallets (
    WalletID INTEGER PRIMARY KEY AUTOINCREMENT,
    UserID INTEGER NOT NULL,
    Balance REAL NOT NULL DEFAULT 0.0,
    Currency TEXT DEFAULT 'USD'
);

CREATE TABLE IF NOT EXISTS Transactions (
    TransactionID INTEGER PRIMARY KEY AUTOINCREMENT,
    WalletID INTEGER NOT NULL,
    OrderID INTEGER,
    Amount REAL NOT NULL,
    Type TEXT NOT NULL,
    Timestamp TEXT NOT NULL,
    FOREIGN KEY (WalletID) REFERENCES Wallets(WalletID)
);

CREATE TABLE IF NOT EXISTS PaymentMethods (
    MethodID INTEGER PRIMARY KEY AUTOINCREMENT,
    WalletID INTEGER NOT NULL,
    Provider TEXT NOT NULL,
    ExpiryDate TEXT,
    FOREIGN KEY (WalletID) REFERENCES Wallets(WalletID)
);

CREATE INDEX IF NOT EXISTS idx_wallets_userid ON Wallets(UserID);
CREATE INDEX IF NOT EXISTS idx_transactions_orderid ON Transactions(OrderID);
CREATE INDEX IF NOT EXISTS idx_transactions_walletid ON Transactions(WalletID);
