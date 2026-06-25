-- Phase 2, Part 3 — asking the data questions with SQL.
--
-- Every query is built from the same shape, added to step by step:
--   SELECT <columns>  FROM <table>  [WHERE <filter>]  [GROUP BY ...]  [ORDER BY ...]

-- 1) Simplest possible query: how many earthquakes do we have?
SELECT count(*) AS total_quakes
FROM staging.events;

-- 2) Choose columns, sort them, keep only the top few: the 5 strongest quakes.
SELECT event_time, magnitude, place
FROM staging.events
ORDER BY magnitude DESC
LIMIT 5;

-- 3) WHERE = keep only rows that match a condition. How many "major" quakes (M7+)?
SELECT count(*) AS major_quakes_m7plus
FROM staging.events
WHERE magnitude >= 7;

-- 4) Another filter: how many quakes triggered a tsunami flag?
SELECT count(*) AS tsunami_flagged
FROM staging.events
WHERE tsunami = 1;

-- 5) GROUP BY = bucket rows together and summarise each bucket.
--    Count quakes per year — our first look at the "is activity increasing?" question.
SELECT date_part('year', event_time)::int AS year,
       count(*)                            AS quakes
FROM staging.events
GROUP BY year
ORDER BY year;
