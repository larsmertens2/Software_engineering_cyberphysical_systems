CREATE TABLE IF NOT EXISTS items (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100),
    category VARCHAR(50),
    stock INT DEFAULT 0,
    aisle INT
);

CREATE TABLE IF NOT EXISTS robots (
    id VARCHAR(50) PRIMARY KEY,
    pos_x FLOAT DEFAULT 0,
    pos_y FLOAT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'offline',
    current_aisle INT,
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

INSERT IGNORE INTO items (id, name, category, stock, aisle) VALUES 
('ITM-001', 'Smartphone', 'Electronics', 50, 1),
('ITM-002', 'Koffiezet', 'Kitchen', 20, 3);