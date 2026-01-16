-- CareDesk Database Schema
-- Tickets, TicketMessages, SatisfactionSurveys

CREATE TABLE IF NOT EXISTS Tickets (
    TicketID INTEGER PRIMARY KEY AUTOINCREMENT,
    UserID INTEGER NOT NULL,
    ReferenceID INTEGER,
    IssueType TEXT NOT NULL,
    Status TEXT DEFAULT 'Open',
    CreatedDate TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS TicketMessages (
    MessageID INTEGER PRIMARY KEY AUTOINCREMENT,
    TicketID INTEGER NOT NULL,
    Sender TEXT NOT NULL,
    Content TEXT NOT NULL,
    Timestamp TEXT NOT NULL,
    FOREIGN KEY (TicketID) REFERENCES Tickets(TicketID)
);

CREATE TABLE IF NOT EXISTS SatisfactionSurveys (
    SurveyID INTEGER PRIMARY KEY AUTOINCREMENT,
    TicketID INTEGER NOT NULL,
    Rating INTEGER NOT NULL CHECK(Rating >= 1 AND Rating <= 5),
    Comments TEXT,
    FOREIGN KEY (TicketID) REFERENCES Tickets(TicketID)
);

CREATE INDEX IF NOT EXISTS idx_tickets_userid ON Tickets(UserID);
CREATE INDEX IF NOT EXISTS idx_tickets_referenceid ON Tickets(ReferenceID);
CREATE INDEX IF NOT EXISTS idx_ticketmessages_ticketid ON TicketMessages(TicketID);
