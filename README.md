# Bike Rides Data Warehouse

## Introduction

The bike rides data warehouse is designed to provide a comprehensive view of bike trips and associated station information. The data is stored in a star schema, which allows for easy and efficient querying and reporting of the data. 

## Data sources

1. Historical data of bike rides from Citibike: https://citibikenyc.com/system-data
2. Up-to-date information about citibike stations: https://github.com/MobilityData/gbfs/blob/master/gbfs.md 


## Deployment
Right now Airflow is running in a docker container on an EC2 instance, and I have a bash command that uses SSH to connect to the EC2 server and pulls the latest code when the repository is updated. 

## Data collection information

1. For (1) above, the Airflow job pulls the latest records from the API for that month, unzips the CSV files and stores them in S3. 
2. Then it moves the data from S3 into a staging table into a Redshift cluster
3. Another job also pulls a JSON file from (2) and stores that into a Redshift cluster
4. Finally, we transform the data and create a fact table and two dimensional tables in Redshift.

## Schema

The star schema consists of one fact table and two dimension tables:

1. **Fact table: BikeTrips**
   - trip_id (Primary key, alphanumeric)
   - date_id (Foreign key to Date dimension table)
   - start_station_id (Foreign key to Station dimension table)
   - end_station_id (Foreign key to Station dimension table)
   - started_at (Timestamp of when the trip started)
   - ended_at (Timestamp of when the trip ended)
   - start_lat (Latitude of the start station)
   - start_lng (Longitude of the start station)
   - end_lat (Latitude of the end station)
   - end_lng (Longitude of the end station)
   - member_casual (Type of membership of the rider)

2. **Dimension table: Date**
   - date_id (Primary key)
   - date (Date in YYYY-MM-DD format)
   - day (Day of the month)
   - month (Month of the year)
   - year (Year)
   - weekday (Day of the week)

3. **Dimension table: Station**
   - station_id (Primary key)
   - external_id 
   - electric_bike_surcharge_waiver
   - short_name
   - eightd_has_key_dispenser
   - name
   - lat
   - lon
   - region_id
   - capacity
   - has_kiosk
   - station_type
   - rental_methods
   - legacy_id

## Design

The fact table, `BikeTrips`, is at the center of the schema and contains transactional data about each bike trip, such as when it started and ended, and the location of the start and end stations.

The `Date` dimension table contains a unique row for each date in the data. This allows for efficient querying of the data by various date components, such as day, month, or year.

The `Station` dimension table contains the most up-to-date information about each station. Since each station might have many trips associated with it (both starting and ending), it makes sense to include this in a separate dimension table.

## How to Use

The tables in this schema are designed to work together to provide a comprehensive view of the bike trips data. Here are some examples of how you might use these tables:

- To get a count of trips by day of the week, you could join the `BikeTrips` fact table to the `Date` dimension table on `date_id` and then group by the `weekday` field.
- To get a list of stations with the most trips, you could join the `BikeTrips` fact table to the `Station` dimension table on `start_station_id` and then group by the `station_id` field.
- To see how the number of trips changes over time, you could group the `BikeTrips` fact table by the `date_id` field and then join to the `Date` dimension table to get the actual dates.

This schema is designed to be flexible, so you can easily add more dimensions or facts as your data grows or as your analysis needs change.

## Data Quality Checks
The Airflow task runs a DQ check for each table to make sure it has at least 1 row inserted into it. 

I also explored the data in the Jupyter notebook, checking for duplicate rows and null values. I did not find any duplicate rows. But analysts should be aware of some NULL values for lat and lng as well as station id in the bike_trip_facts table. 


## Data update cycle
The data for rides is updated once a month, which is how often Citibike releases new data. The data for the station information is checked once an hour, since this data is realtime and can change at any time. 

## How to handle other scenarios
If the data was increased by 100x.
- In that case, the information for the data might not fit into a single machine, and I might need to run parallel processing. In that case, I could use Spark run transformations in parallel across multiple machines. 

If the pipelines were run on a daily basis by 7am.
- I would re-do the data so it only updates for the last execution date, instead of re-transforming the entire dataset at once. 

If the database needed to be accessed by 100+ people.
- Right now its running a free version of Redshift serverless. If a large company was regularly querying this data, I might need to increase the compute power for my Redshift cluster, choosing a paid version where I specified the compute power depending on how many queries were being run. 