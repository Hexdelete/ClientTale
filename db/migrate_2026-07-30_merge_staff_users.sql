-- Merges login accounts into staff: every staff member now has exactly one
-- username/password, managed from the Manage Staff page. Drops the standalone
-- `users` table. Adds an 'admin' staff role for accounts with no lawyer/
-- paralegal function (e.g. the seeded admin login).
--
-- Existing staff with no linked login get an auto-created one:
--   username = lowercase "firstname.lastname"
--   password = "password123" (they should change it after first sign-in)
--
-- Apply with:
--   docker exec -i clienttale-db-1 mysql -u root -p"$MYSQL_ROOT_PASSWORD" clienttale < db/migrate_2026-07-30_merge_staff_users.sql
--
-- NOTE: replace TEMP_PASSWORD_HASH below with the output of:
--   python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('password123'))"

USE clienttale;

ALTER TABLE staff
    MODIFY role ENUM('lawyer', 'paralegal', 'admin') NOT NULL;

ALTER TABLE staff
    ADD COLUMN username VARCHAR(100) NULL AFTER role,
    ADD COLUMN password_hash VARCHAR(255) NULL AFTER username;

-- Backfill from any users already linked to a staff row.
UPDATE staff s
JOIN users u ON u.staff_id = s.id
SET s.username = u.username, s.password_hash = u.password_hash;

-- Users with no staff link become admin-role staff rows.
INSERT INTO staff (first_name, last_name, role, username, password_hash, active)
SELECT 'Admin', 'User', 'admin', u.username, u.password_hash, 1
FROM users u
WHERE u.staff_id IS NULL;

-- Any staff still missing a login get a temporary one.
UPDATE staff
SET username = LOWER(CONCAT(first_name, '.', last_name)),
    password_hash = 'TEMP_PASSWORD_HASH'
WHERE username IS NULL;

ALTER TABLE staff
    ADD UNIQUE KEY uq_staff_username (username);

ALTER TABLE staff
    MODIFY username VARCHAR(100) NOT NULL,
    MODIFY password_hash VARCHAR(255) NOT NULL;

ALTER TABLE users DROP FOREIGN KEY fk_users_staff;
DROP TABLE users;
