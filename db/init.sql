-- Law Client Tracking System - schema and seed data
-- Loaded automatically by the MySQL container on first start
-- (mounted at /docker-entrypoint-initdb.d)

CREATE DATABASE IF NOT EXISTS clienttale;
USE clienttale;

-- ---------------------------------------------------------------------------
-- staff: lawyers, paralegals, and admins. Every staff member has a login.
-- Lawyers/paralegals populate the dropdowns in the case file.
-- ---------------------------------------------------------------------------
CREATE TABLE staff (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    first_name    VARCHAR(100) NOT NULL,
    last_name     VARCHAR(100) NOT NULL,
    role          ENUM('lawyer', 'paralegal', 'admin') NOT NULL,
    email         VARCHAR(255) NULL,
    username      VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    active        TINYINT(1) NOT NULL DEFAULT 1,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- cases: mirrors every field on the FileMaker "Case Intake Form" PDF
-- ---------------------------------------------------------------------------
CREATE TABLE cases (
    id                    INT AUTO_INCREMENT PRIMARY KEY,

    -- Case Data
    case_number           VARCHAR(50) NOT NULL UNIQUE,
    status                VARCHAR(50) NOT NULL DEFAULT 'Pending',
    case_type             VARCHAR(50),
    date_of_event         DATE,
    sol_date              DATE,
    conf_int_check_date   DATE,
    county                VARCHAR(100),
    judge                 VARCHAR(255),

    -- Staff assignment
    primary_lawyer_id     INT NULL,
    secondary_lawyer_id   INT NULL,
    legal_assistant_id    INT NULL,

    -- Injured person
    injured_first_name    VARCHAR(100),
    injured_last_name     VARCHAR(100),
    dob                   DATE,
    dod                   DATE,
    ssn                   VARCHAR(20),
    age                   INT,
    height                VARCHAR(20),
    weight                VARCHAR(20),

    -- Contact Data / client
    client_first_name     VARCHAR(100),
    client_last_name      VARCHAR(100),
    address_line1         VARCHAR(255),
    address_line2         VARCHAR(255),
    city                  VARCHAR(100),
    state                 VARCHAR(20),
    zip                   VARCHAR(20),
    country               VARCHAR(100),
    work_phone            VARCHAR(50),
    email                 VARCHAR(255),

    -- Narrative
    case_synopsis         TEXT,
    intake_comments       TEXT,

    created_at            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_cases_primary_lawyer   FOREIGN KEY (primary_lawyer_id)   REFERENCES staff(id) ON DELETE SET NULL,
    CONSTRAINT fk_cases_secondary_lawyer FOREIGN KEY (secondary_lawyer_id) REFERENCES staff(id) ON DELETE SET NULL,
    CONSTRAINT fk_cases_legal_assistant  FOREIGN KEY (legal_assistant_id)  REFERENCES staff(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- case_events: depositions, filings, hearings, deadlines, etc.
-- ---------------------------------------------------------------------------
CREATE TABLE case_events (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    case_id      INT NOT NULL,
    event_type   VARCHAR(100) NOT NULL,
    event_date   DATE NOT NULL,
    event_time   TIME NULL,
    description  VARCHAR(500),
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_events_case FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_case_events_date ON case_events(event_date);
CREATE INDEX idx_cases_status ON cases(status);

-- ---------------------------------------------------------------------------
-- opposing_counsel: a case may have zero, one, or several opposing counsel
-- ---------------------------------------------------------------------------
CREATE TABLE opposing_counsel (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    case_id      INT NOT NULL,
    name         VARCHAR(255),
    firm         VARCHAR(255),
    phone        VARCHAR(50),
    email        VARCHAR(255),
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_opposing_counsel_case FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Seed: single admin staff login (username: admin / password: changeme123)
-- Password hash generated with Werkzeug's generate_password_hash().
-- CHANGE THIS PASSWORD after first login (Manage Staff page).
-- ---------------------------------------------------------------------------
INSERT INTO staff (first_name, last_name, role, username, password_hash, active) VALUES
('Admin', 'User', 'admin', 'admin', 'scrypt:32768:8:1$pT5RGJKZ6cpFTy5B$19e3080359fea94a03553b7e529fad1a0f801259183d4dee70c6377ae66fef42b7f3c79822c870e56b629ee344fbc0447a5a47c730aa97f96c55c5887498ce9c', 1);
