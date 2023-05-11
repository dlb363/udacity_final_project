CREATE_TRIPS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS trips (
ride_id VARCHAR NOT NULL,
rideable_type VARCHAR,
started_at VARCHAR,
ended_at VARCHAR,
start_station_name VARCHAR,
start_station_id VARCHAR,
end_station_name VARCHAR,
end_station_id VARCHAR,
start_lat DECIMAL(9,6),
start_lng DECIMAL(9,6),
end_lat DECIMAL(9,6),
end_lng DECIMAL(9,6),
member_casual VARCHAR,
PRIMARY KEY(ride_id))
DISTSTYLE AUTO;
"""

CREATE_REALTIME_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS station_information (
    external_id VARCHAR,
    station_id VARCHAR,
    electric_bike_surcharge_waiver BOOLEAN,
    short_name VARCHAR,
    eightd_has_key_dispenser BOOLEAN,
    name VARCHAR,
    lat DECIMAL(9,6),
    region_id VARCHAR,
    lon DECIMAL(9,6),
    capacity INT,
    has_kiosk BOOLEAN,
    station_type VARCHAR,
    rental_methods VARCHAR,
    legacy_id VARCHAR
);
"""


CREATE_DATE_DIMENSION_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS date_dimension (
    date_id INT NOT NULL,
    date DATE,
    day INT,
    month INT,
    year INT,
    weekday INT,
    PRIMARY KEY(date_id))
DISTSTYLE AUTO;
"""

INSERT_DATE_DIMENSION_TABLE_SQL = """
INSERT INTO date_dimension(date_id, date, day, month, year, weekday)
SELECT DISTINCT 
    TO_CHAR(TO_DATE(started_at, 'YYYY-MM-DD'), 'YYYYMMDD')::INT AS date_id,
    TO_DATE(started_at, 'YYYY-MM-DD') AS date,
    EXTRACT(DAY FROM TO_DATE(started_at, 'YYYY-MM-DD'))::INT AS day,
    EXTRACT(MONTH FROM TO_DATE(started_at, 'YYYY-MM-DD'))::INT AS month,
    EXTRACT(YEAR FROM TO_DATE(started_at, 'YYYY-MM-DD'))::INT AS year,
    EXTRACT(DOW FROM TO_DATE(started_at, 'YYYY-MM-DD'))::INT AS weekday
FROM trips;
"""


CREATE_STATION_DIMENSION_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS station_dimension (
    station_id VARCHAR NOT NULL,
    external_id VARCHAR,
    electric_bike_surcharge_waiver BOOLEAN,
    short_name VARCHAR,
    eightd_has_key_dispenser BOOLEAN,
    name VARCHAR,
    lat DECIMAL(9,6),
    lon DECIMAL(9,6),
    region_id VARCHAR,
    capacity INT,
    has_kiosk BOOLEAN,
    station_type VARCHAR,
    rental_methods VARCHAR,
    legacy_id VARCHAR,
    PRIMARY KEY(station_id))
DISTSTYLE AUTO;
"""

INSERT_STATION_DIMENSION_TABLE_SQL = """
INSERT INTO station_dimension
SELECT * FROM station_information;
"""



CREATE_BIKETRIPS_FACT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS biketrips_fact (
    trip_id VARCHAR NOT NULL,
    date_id INT,
    start_station_id VARCHAR,
    end_station_id VARCHAR,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    start_lat DECIMAL(9,6),
    start_lng DECIMAL(9,6),
    end_lat DECIMAL(9,6),
    end_lng DECIMAL(9,6),
    member_casual VARCHAR,
    PRIMARY KEY(trip_id),
    FOREIGN KEY (date_id) REFERENCES date_dimension(date_id),
    FOREIGN KEY (start_station_id) REFERENCES station_dimension(station_id),
    FOREIGN KEY (end_station_id) REFERENCES station_dimension(station_id))
DISTSTYLE AUTO;
"""

INSERT_BIKETRIPS_FACT_TABLE_SQL = """
INSERT INTO biketrips_fact(trip_id, date_id, start_station_id, end_station_id, started_at, ended_at, start_lat, start_lng, end_lat, end_lng, member_casual)
SELECT 
    ride_id AS trip_id,
    TO_CHAR(TO_DATE(started_at, 'YYYY-MM-DD'), 'YYYYMMDD')::INT AS date_id,
    start_station_id,
    end_station_id,
    TO_TIMESTAMP(started_at, 'YYYY-MM-DD HH24:MI:SS') AS started_at,
    TO_TIMESTAMP(ended_at, 'YYYY-MM-DD HH24:MI:SS') AS ended_at,
    start_lat,
    start_lng,
    end_lat,
    end_lng,
    member_casual
FROM trips;
"""

# Define deletion SQL statements
DELETE_DATE_DIMENSION_TABLE_SQL = """DELETE FROM date_dimension;"""
DELETE_STATION_DIMENSION_TABLE_SQL = """DELETE FROM station_dimension;"""
DELETE_BIKETRIPS_FACT_TABLE_SQL = """DELETE FROM biketrips_fact;"""
