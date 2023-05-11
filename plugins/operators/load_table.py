from airflow.hooks.postgres_hook import PostgresHook
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

class LoadTableOperator(BaseOperator):

    ui_color = '#F98866'

    @apply_defaults
    def __init__(self,
                redshift_conn_id = "",
                table = "",
                sql = "",        
                append_only = True,
                *args, **kwargs):

        super(LoadTableOperator, self).__init__(*args, **kwargs)
        self.redshift_conn_id = redshift_conn_id
        self.table = table
        self.sql = sql
        self.append_only = append_only

    def execute(self, context):
        self.log.info('LoadFactOperator not implemented yet')
        redshift = PostgresHook(postgres_conn_id=self.redshift_conn_id)

        if self.append_only == False:
            self.log.info(f"Deleting from {self.table}")
            redshift.run(f"DELETE FROM {self.table}") 
        self.log.info(f"Insert data from staging tables into {self.table}")
        insert_statement = f"INSERT INTO {self.table} \n{self.sql}"
        redshift.run(insert_statement)
        self.log.info(f"Finished inserting into {self.table}")