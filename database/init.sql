CREATE TABLE IF NOT EXISTS items (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100),
    category VARCHAR(50),
    stock INT DEFAULT 0,
    aisle INT
);


INSERT IGNORE INTO items (id, name, category, stock, aisle) VALUES 
('ITM-001', 'Smartphone', 'Electronics', 50, 1),
('ITM-002', 'Koffiezet', 'Kitchen', 20, 3);