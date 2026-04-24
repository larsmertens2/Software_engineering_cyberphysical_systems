DROP TABLE IF EXISTS items; 

CREATE TABLE items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    stock INT DEFAULT 0,
    aisle INT
);

CREATE TABLE IF NOT EXISTS job_queue (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT NOT NULL,
    status ENUM('pending', 'assigned', 'completed') DEFAULT 'pending',
    robot_id VARCHAR(50) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES items(id)
);


INSERT INTO items (name, category, stock, aisle) VALUES 
('Smartphone', 'Electro', 50, 1),
('Koffiezet', 'Keukengerief', 20, 3),
('Laptop Stand', 'Electro', 15, 2),
('Draadloze Muis', 'Electro', 30, 2),
('Waterkoker', 'Keuken', 10, 3),
('Bureaustoel', 'Meubilair', 5, 4),
('LED Strip', 'Home Improvement', 100, 5),
('Monitor Arm', 'Electro', 12, 2);


INSERT INTO job_queue (item_id) VALUES 
(1), -- Smartphone (Aisle 1)
(2), -- Koffiezet (Aisle 3)
(4), -- Draadloze Muis (Aisle 2)
(6), -- Bureaustoel (Aisle 4)
(1); -- Nog een Smartphone