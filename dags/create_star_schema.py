from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.postgres_operator import PostgresOperator
import sql_statements
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
    "create_start_schema",
    default_args=default_args,
    description="Create fact and dim tables from staging tables",
    schedule_interval=timedelta(days=30),
    start_date=datetime(2023, 4, 1),
    catchup=False,
    concurrency=1, 
    max_active_runs=1,
)

# Task to create the date dim table in Redshift
create_date_dim_table = PostgresOperator(
    task_id="create_date_dim_table",
    postgres_conn_id="redshift",
    sql=sql_statements.CREATE_DATE_DIMENSION_TABLE_SQL,
    dag=dag,
)

insert_date_dim_table = PostgresOperator(
    task_id="insert_date_dim_table",
    postgres_conn_id="redshift",
    sql=sql_statements.INSERT_DATE_DIMENSION_TABLE_SQL,
    dag=dag,
)

# Task to create the station dim table in Redshift
create_station_dim_table = PostgresOperator(
    task_id="create_station_dim_table",
    postgres_conn_id="redshift",
    sql=sql_statements.CREATE_STATION_DIMENSION_TABLE_SQL,
    dag=dag,
)

# Task to insert data into the station dim table in Redshift
insert_station_dim_table = PostgresOperator(
    task_id="insert_station_dim_table",
    postgres_conn_id="redshift",
    sql=sql_statements.INSERT_STATION_DIMENSION_TABLE_SQL,
    dag=dag,
)

# Task to create the biketrips fact table in Redshift
create_biketrips_fact_table = PostgresOperator(
    task_id="create_biketrips_fact_table",
    postgres_conn_id="redshift",
    sql=sql_statements.CREATE_BIKETRIPS_FACT_TABLE_SQL,
    dag=dag,
)

# Task to insert data into the biketrips fact table in Redshift
insert_biketrips_fact_table = PostgresOperator(
    task_id="insert_biketrips_fact_table",
    postgres_conn_id="redshift",
    sql=sql_statements.INSERT_BIKETRIPS_FACT_TABLE_SQL,
    dag=dag,
)

# Define deletion tasks
delete_date_dim_table = PostgresOperator(
    task_id="delete_date_dim_table",
    postgres_conn_id="redshift",
    sql=sql_statements.DELETE_DATE_DIMENSION_TABLE_SQL,
    dag=dag,
)

delete_station_dim_table = PostgresOperator(
    task_id="delete_station_dim_table",
    postgres_conn_id="redshift",
    sql=sql_statements.DELETE_STATION_DIMENSION_TABLE_SQL,
    dag=dag,
)

delete_biketrips_fact_table = PostgresOperator(
    task_id="delete_biketrips_fact_table",
    postgres_conn_id="redshift",
    sql=sql_statements.DELETE_BIKETRIPS_FACT_TABLE_SQL,
    dag=dag,
)

# Data Quality Check for the date_dimension table
date_dim_data_quality_check = DataQualityOperator(
    task_id='date_dim_data_quality_check',
    dag=dag,
    conn_id="redshift",
    sql_check_query="""
        SELECT COUNT(*) FROM date_dimension
    """,
    expected_results=lambda records_count: records_count > 0
)

# Data Quality Check for the station_dimension table
station_dim_data_quality_check = DataQualityOperator(
    task_id='station_dim_data_quality_check',
    dag=dag,
    conn_id="redshift",
    sql_check_query="""
        SELECT COUNT(*) FROM station_dimension
    """,
    expected_results=lambda records_count: records_count > 0
)

# Data Quality Check for the biketrips_fact table
biketrips_fact_data_quality_check = DataQualityOperator(
    task_id='biketrips_fact_data_quality_check',
    dag=dag,
    conn_id="redshift",
    sql_check_query="""
        SELECT COUNT(*) FROM biketrips_fact
    """,
    expected_results=lambda records_count: records_count > 0
)


# Define the order in which the tasks will run
# Define creation tasks
creation_tasks = [
    create_date_dim_table,
    create_station_dim_table,
    create_biketrips_fact_table
]

# Define insertion tasks
insertion_tasks = [
    insert_date_dim_table,
    insert_station_dim_table,
    insert_biketrips_fact_table
]

# Define data quality checks
data_quality_checks = [
    date_dim_data_quality_check,
    station_dim_data_quality_check,
    biketrips_fact_data_quality_check
]

# Define deletion tasks in a list
deletion_tasks = [
    delete_date_dim_table,
    delete_station_dim_table,
    delete_biketrips_fact_table
]

# Define task dependencies
for create, delete, insert, check in zip(creation_tasks, deletion_tasks, insertion_tasks, data_quality_checks):
    create >> delete >> insert >> check
