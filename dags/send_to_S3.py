import datetime

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.hooks.S3_hook import S3Hook
import os


import zipfile
from tempfile import NamedTemporaryFile
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup 
import re


def get_list_of_zip_urls(base_api_url, current_year, current_month):
    response = requests.get(base_api_url)
    bs_data = BeautifulSoup(response.content, 'xml')
    date_pattern = re.compile(r'{}{}'.format(current_year, current_month))
    
    print("pattern_match", date_pattern)
    urls = []
    for key in bs_data.find_all('Contents'):
        url = base_api_url + key.find('Key').text
        print("checking url", url)
        if url.split(".")[-1] == 'zip' and date_pattern.search(url) and 'JC' not in url:
            urls.append(url)
    return urls

def download_and_store_csv(url, s3_bucket, current_year, current_month):
    response = requests.get(url)

    with NamedTemporaryFile(delete=False) as zip_temp:
        zip_temp.write(response.content)
        zip_temp.flush()

    try:
        with zipfile.ZipFile(zip_temp.name, 'r') as zip_ref:
            file = zip_ref.namelist()[0]
            print('file name', file)
            with NamedTemporaryFile(delete=False) as csv_temp:
                with zip_ref.open(file, 'r') as csv_file:
                    csv_temp.write(csv_file.read())
                    csv_temp.flush()
                    print("file size =", os.stat(csv_temp.name).st_size)
                try:
                            s3_hook = S3Hook(aws_conn_id='aws_credentials')
                            print('csv S3 name', csv_temp.name)
                            s3_hook.load_file(
                                filename=csv_temp.name,
                                key=f'{current_year}/{current_month}/citibike_monthly_data.csv',
                                bucket_name=s3_bucket,
                                replace=True
                            )
                finally:
                            os.remove(csv_temp.name)
    finally:
        os.remove(zip_temp.name)

def process_urls(**kwargs):
    base_api_url = kwargs['base_api_url']
    s3_bucket = kwargs['s3_bucket']
    execution_date = kwargs['ti'].execution_date
    current_year = execution_date.year
    current_month = execution_date.strftime('%m')
    print("year, month", current_year, current_month)
    urls = get_list_of_zip_urls(base_api_url, current_year, current_month)
    print(urls)
    print("url len", len(urls))
    for url in urls:
        download_and_store_csv(url, s3_bucket, current_year, current_month)


default_args = {
    'owner': 'devonbancroft',
    'depends_on_past': False,
    'start_date': datetime(2013, 7, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'max_active_runs': 1,
    'retry_delay': timedelta(minutes=1),
}

base_api_url = 'https://s3.amazonaws.com/tripdata/'
s3_bucket = 'devonbancroft-citibike'

dag = DAG(
        'citibike_api_unzip_and_store_in_s3',
        default_args=default_args,
        schedule_interval='0 0 * * SUN',
        catchup=True,
        concurrency=1,
        )

list_task = PythonOperator(
    task_id="process_urls",
    python_callable=process_urls,
    op_kwargs={'base_api_url': base_api_url, 's3_bucket': s3_bucket},
    provide_context=True,
    dag=dag,
)