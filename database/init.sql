DROP TABLE IF EXISTS items; 

CREATE TABLE items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    stock INT DEFAULT 0,
    aisle INT
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