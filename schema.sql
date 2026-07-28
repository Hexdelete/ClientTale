CREATE TABLE IF NOT EXISTS staff (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS cases (
    id INT AUTO_INCREMENT PRIMARY KEY,
    case_number VARCHAR(50) NOT NULL UNIQUE,
    case_title VARCHAR(150) NOT NULL,
    client_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'Active',
    lawyer_id INT,
    paralegal_id INT,
    FOREIGN KEY (lawyer_id) REFERENCES staff(id) ON DELETE SET NULL,
    FOREIGN KEY (paralegal_id) REFERENCES staff(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS critical_dates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    case_id INT NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    title VARCHAR(150) NOT NULL,
    event_date DATE NOT NULL,
    notes TEXT,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
);