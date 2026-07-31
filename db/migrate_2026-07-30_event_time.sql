-- Adds an optional time-of-day to case events.
-- Additive/nullable only — safe to run against an existing database.
-- Apply with:
--   docker exec -i clienttale-db-1 mysql -u root -p"$MYSQL_ROOT_PASSWORD" clienttale < db/migrate_2026-07-30_event_time.sql

USE clienttale;

ALTER TABLE case_events
    ADD COLUMN event_time TIME NULL AFTER event_date;
