-- Turns opposing counsel into a per-case list (a case may have zero, one, or
-- several opposing counsel entries) instead of a single fixed set of columns.
-- Migrates any existing single-record data into the new table, then drops
-- the old columns.
--
-- Apply with:
--   docker exec -i clienttale-db-1 mysql -u root -p"$MYSQL_ROOT_PASSWORD" clienttale < db/migrate_2026-07-30_opposing_counsel_list.sql

USE clienttale;

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

INSERT INTO opposing_counsel (case_id, name, firm, phone, email)
SELECT id, opposing_counsel_name, opposing_counsel_firm, opposing_counsel_phone, opposing_counsel_email
FROM cases
WHERE opposing_counsel_name IS NOT NULL
   OR opposing_counsel_firm IS NOT NULL
   OR opposing_counsel_phone IS NOT NULL
   OR opposing_counsel_email IS NOT NULL;

ALTER TABLE cases
    DROP COLUMN opposing_counsel_name,
    DROP COLUMN opposing_counsel_firm,
    DROP COLUMN opposing_counsel_phone,
    DROP COLUMN opposing_counsel_email;
