from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
from operators.data_quality import DataQualityOperator
from sql_statements import CREATE_REALTIME_TABLE_SQL

import json
import requests

def load_data_to_redshift(*args, **kwargs):
    url = "https://gbfs.citibikenyc.com/gbfs/en/station_information.json"
    response = requests.get(url)
    data = response.json()['data']['stations']

    pg_hook = PostgresHook(postgres_conn_id="redshift")
    conn = pg_hook.get_conn()
    cursor = conn.cursor()

    # Clear the table
    cursor.execute("TRUNCATE station_information;")
    conn.commit()

    for record in data:
        try:
            record = {k: v if v is not None else 'NULL' for k, v in record.items()}
            record = {k: v.replace("'", "''") if isinstance(v, str) else v for k, v in record.items()}
            insert_query = f"""
            INSERT INTO station_information (
                external_id, station_id, electric_bike_surcharge_waiver, 
                short_name, eightd_has_key_dispenser, name, lat, 
                region_id, lon, capacity, has_kiosk, station_type, 
                rental_methods, legacy_id
            )
            VALUES (
                '{record['external_id']}', '{record['station_id']}', {record['electric_bike_surcharge_waiver']},
                '{record['short_name']}', {record['eightd_has_key_dispenser']}, '{record['name']}', {record['lat']},
                '{record['region_id']}', {record['lon']}, {record['capacity']}, {record['has_kiosk']},
                '{record['station_type']}', '{",".join(record['rental_methods'])}', '{record['legacy_id']}'
            );
            """
            cursor.execute(insert_query)
        except KeyError:
            print(f"skipping record {record} with bad data")
    conn.commit()

default_args = {
    'owner': 'airflow',
    'start_date': days_ago(2),
}

with DAG(
    'load_realtime_data_to_redshift',
    schedule_interval='@hourly',
    default_args=default_args,
    description='Load realtime bike station data to Redshift',
    catchup=False
) as dag:
    
    create_table = PostgresOperator(
        task_id="create_table",
        postgres_conn_id="redshift",
        sql=CREATE_REALTIME_TABLE_SQL,
    )

    load_data = PythonOperator(
        task_id='load_data_to_redshift',
        python_callable=load_data_to_redshift,
    )

    realtime_count_data_quality_check = DataQualityOperator(
        task_id='realtime_count_data_quality_check',
        dag=dag,
        conn_id="redshift",
        sql_check_query="""
            SELECT COUNT(*) FROM station_information
        """,
        expected_results=lambda records_count: records_count > 0
    )

    create_table >> load_data >> realtime_count_data_quality_check

