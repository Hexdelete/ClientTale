-- Adds staff email and opposing counsel contact fields.
-- Additive/nullable only — safe to run against an existing database.
-- Apply with:
--   docker exec -i clienttale-db-1 mysql -u root -p"$MYSQL_ROOT_PASSWORD" clienttale < db/migrate_2026-07-30_email_opposing_counsel.sql

USE clienttale;

ALTER TABLE staff
    ADD COLUMN email VARCHAR(255) NULL AFTER role;

ALTER TABLE cases
    ADD COLUMN opposing_counsel_name  VARCHAR(255) NULL AFTER email,
    ADD COLUMN opposing_counsel_firm  VARCHAR(255) NULL AFTER opposing_counsel_name,
    ADD COLUMN opposing_counsel_phone VARCHAR(50)  NULL AFTER opposing_counsel_firm,
    ADD COLUMN opposing_counsel_email VARCHAR(255) NULL AFTER opposing_counsel_phone;
