-- ShipStream Database Schema
-- Shipments, Warehouses, TrackingEvents

CREATE TABLE IF NOT EXISTS Shipments (
    ShipmentID INTEGER PRIMARY KEY AUTOINCREMENT,
    OrderID INTEGER NOT NULL,
    TrackingNumber TEXT NOT NULL UNIQUE,
    EstimatedArrival TEXT NOT NULL,
    Status TEXT DEFAULT 'In Transit'
);

CREATE TABLE IF NOT EXISTS Warehouses (
    WarehouseID INTEGER PRIMARY KEY AUTOINCREMENT,
    Location TEXT NOT NULL,
    ManagerName TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS TrackingEvents (
    EventID INTEGER PRIMARY KEY AUTOINCREMENT,
    ShipmentID INTEGER NOT NULL,
    WarehouseID INTEGER,
    Timestamp TEXT NOT NULL,
    StatusUpdate TEXT NOT NULL,
    FOREIGN KEY (ShipmentID) REFERENCES Shipments(ShipmentID),
    FOREIGN KEY (WarehouseID) REFERENCES Warehouses(WarehouseID)
);

CREATE INDEX IF NOT EXISTS idx_shipments_orderid ON Shipments(OrderID);
CREATE INDEX IF NOT EXISTS idx_trackingevents_shipmentid ON TrackingEvents(ShipmentID);
