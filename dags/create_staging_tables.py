from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.postgres_operator import PostgresOperator
from operators.s3_to_redshift import S3ToRedshiftOperator
from sql_statements import CREATE_TRIPS_TABLE_SQL
from operators.data_quality import DataQualityOperator


# Define default arguments for the DAG
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}

# Instantiate the DAG object
dag = DAG(
    "load_trips_data",
    default_args=default_args,
    description="Load trips data from S3 to Redshift",
    schedule_interval=timedelta(days=30),
    start_date=datetime(2022, 1, 1),
    catchup=True,
    concurrency=1, 
    max_active_runs=1,
)

# Task to create the trips table in Redshift
create_trips_table = PostgresOperator(
    task_id="create_trips_table",
    postgres_conn_id="redshift",
    sql=CREATE_TRIPS_TABLE_SQL,
    dag=dag,
)

# Task to load data from S3 to Redshift
load_data_from_s3_to_redshift = S3ToRedshiftOperator(
    task_id="load_data_from_s3_to_redshift",
    postgres_conn_id="redshift",
    aws_credentials_id="aws_credentials",
    table="trips",
    s3_bucket="devonbancroft-citibike",
    s3_key="{{ execution_date.strftime('%Y') }}/{{ execution_date.strftime('%m') }}/citibike_monthly_data.csv",
    delimiter=",",
    ignore_headers=1,
    dag=dag,
)

# DQ check
staging_count_data_quality_check = DataQualityOperator(
        task_id='staging_count_data_quality_check',
        dag=dag,
        conn_id="redshift",
        sql_check_query="""
            SELECT COUNT(*) FROM trips
        """,
        expected_results=lambda records_count: records_count > 0
    )



# Set task dependencies
create_trips_table >> load_data_from_s3_to_redshift >> staging_count_data_quality_check
