-- Phase 2, Part 2 — build the clean "staging" table from the raw JSON.
--
-- Each row in raw.events holds ONE earthquake as JSONB (nested JSON). Below we
-- pull out the useful fields, give each a proper data type (a date is a date, a
-- number is a number), and save them as plain, flat columns in staging.events.
--
-- JSON operators used here:
--   ->   gets a piece and keeps it as JSON   (e.g. raw -> 'properties')
--   ->>  gets a piece as plain text          (e.g. ... ->> 'mag'  ->  "5.0")
--   ::   converts text into another type     (e.g. '5.0'::numeric ->  5.0)

DROP TABLE IF EXISTS staging.events;

CREATE TABLE staging.events AS
SELECT
    raw ->> 'id'                                                     AS id,
    to_timestamp((raw -> 'properties' ->> 'time')::bigint / 1000.0)  AS event_time,
    (raw -> 'properties' ->> 'mag')::numeric                         AS magnitude,
     raw -> 'properties' ->> 'magType'                               AS mag_type,
     raw -> 'properties' ->> 'place'                                 AS place,
    (raw -> 'geometry'   -> 'coordinates' ->> 0)::numeric            AS longitude,
    (raw -> 'geometry'   -> 'coordinates' ->> 1)::numeric            AS latitude,
    (raw -> 'geometry'   -> 'coordinates' ->> 2)::numeric            AS depth_km,
    (raw -> 'properties' ->> 'tsunami')::int                         AS tsunami,
    (raw -> 'properties' ->> 'felt')::int                            AS felt_reports,
    (raw -> 'properties' ->> 'sig')::int                             AS significance,
     raw -> 'properties' ->> 'net'                                   AS network
FROM raw.events;

-- Indexes make common questions (by time, by size, by location) fast.
CREATE INDEX idx_events_time ON staging.events (event_time);
CREATE INDEX idx_events_mag  ON staging.events (magnitude);
CREATE INDEX idx_events_geo  ON staging.events (latitude, longitude);
