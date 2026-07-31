-- Removes fields the firm doesn't use: Date of Contact, Referral Source,
-- Date Declined, Who Declined, How Declined. Also drops the "In Litigation"
-- status value from any existing rows (falls back to "Open") since it's no
-- longer offered on the form.
--
-- Apply with:
--   docker exec -i clienttale-db-1 mysql -u root -p"$MYSQL_ROOT_PASSWORD" clienttale < db/migrate_2026-07-31_drop_unused_case_fields.sql

USE clienttale;

UPDATE cases SET status = 'Open' WHERE status = 'In Litigation';

ALTER TABLE cases
    DROP COLUMN date_of_contact,
    DROP COLUMN referral_source,
    DROP COLUMN date_declined,
    DROP COLUMN who_declined,
    DROP COLUMN how_declined;
