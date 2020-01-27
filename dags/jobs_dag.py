import uuid
from datetime import datetime
from datetime import timedelta
import airflow
from airflow.models import DAG
from airflow.hooks.postgres_hook import PostgresHook
from airflow.operators.postgres_operator import PostgresOperator
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.python_operator import BranchPythonOperator

postgres_def_conn_id = 'postres_abetest'
postgres_def_schema_name = 'public'

config = {
    'GRIDU_abe_job_dag_id_1': {'schedule_interval': None, 'start_date': airflow.utils.dates.days_ago(2), 'schema_name':'public', 'table_name': 'abe_job_1'},
    'GRIDU_abe_job_dag_id_2': {'schedule_interval': None, 'start_date': airflow.utils.dates.days_ago(3), 'schema_name':'public', 'table_name': 'abe_job_2'},
    'GRIDU_abe_job_dag_id_3': {'schedule_interval': None, 'start_date': airflow.utils.dates.days_ago(4), 'schema_name':'public', 'table_name': 'abe_job_3'}
}


default_args = {
   'owner': 'Airflow',
   'start_date': datetime(2020, 1, 1)
}

#def check_table_exist():
#   """ method to check that table exists """
##   if True:
#               return 'skip_table_creation'
#   else:
#       return 'create_table'
# for dict in config:
#    #  for param in dict:
#    print(config[dict])

# with DAG('gridu_dag', default_args=default_args, schedule_interval='@once') as dag:
#    pass
def push_xcom_end_job(**kwargs):
    kwargs['ti'].xcom_push(key='job_result', value=f'{kwargs["run_id"]} of {kwargs["ti"]} ended') #kwargs['dag_id']+

def push_xcom_query(**kwargs):
    hook = PostgresHook(postgres_conn_id=kwargs['postgres_conn_id'])
    sql4query = 'SELECT COUNT(*) cnt FROM {};'.format(kwargs['table_name'])
    print('sql4query'+sql4query)
    query = hook.get_first(sql=sql4query)
    print('Query' + str(query))
    for result  in query:
        jobresult = result
        break
    kwargs['ti'].xcom_push(key='query_result', value=f'COUNT= {jobresult}') #kwargs['dag_id']+

def check_table_exist(postgres_conn_id, schema_name, table_name):
        """ callable function to get schema name and after that check if table exist """
        sql_to_check_table_exist = "SELECT * FROM information_schema.tables WHERE table_schema = '{}' AND table_name = '{}';"
        hook = PostgresHook(postgres_conn_id=postgres_conn_id)
        # check table exist
        sqlwithliterals = sql_to_check_table_exist.format(schema_name, table_name)
        print('SQL:'+sqlwithliterals)
        query = hook.get_first(sql=sqlwithliterals)
        print('Query'+str(query))
        if query:
            return 'skip_table_creation'
        else:
            return 'create_table'

def create_dag(dag_id, dagconf, default_args):
    table_name = dagconf.get('table_name')
    sql4create = f'CREATE TABLE {table_name} (custom_id integer NOT NULL, user_name VARCHAR (50) NOT NULL, timestamp TIMESTAMP NOT NULL);'
    sql4insert='INSERT INTO '+table_name+" VALUES (%s, '{{ ti.xcom_pull(task_ids='execute_bash') }}', %s);"
    print('DAG_ID:'+dag_id)
    print('TABLE_NAME:'+ table_name)
    print('SQL4CREATE:'+sql4create)
    print('SQL4INSERT:'+sql4insert)
    with  DAG(
            dag_id=dag_id,
            default_args=default_args,
            start_date=dagconf.get('start_date'),
            schedule_interval=dagconf.get('schedule_interval'),
            dagrun_timeout=timedelta(minutes=240),
    ) as contextdag: (
            PythonOperator(
                task_id='print_process_start',
                python_callable=lambda: print("{dag_id} start processing tables in database: {database}"))
            >> BashOperator(
                task_id='execute_bash',
                bash_command='echo LALA_'+dag_id,
                xcom_push=True)
            >>BranchPythonOperator(
                task_id="check_table_exist",
                python_callable=check_table_exist,
                op_args=[postgres_def_conn_id, postgres_def_schema_name, table_name] #trying op_args usage for research reason
                )
            >>[PostgresOperator(task_id='create_table', postgres_conn_id=postgres_def_conn_id, sql= sql4create),
               DummyOperator(task_id='skip_table_creation')]
            >> PostgresOperator(task_id='insert_new_row', postgres_conn_id=postgres_def_conn_id, trigger_rule='none_failed',
                                sql=sql4insert,  #AWFUL I KNOW %)))
                                parameters=[uuid.uuid4().int % 123456789, datetime.now()])
            >> PythonOperator(task_id='query_new_row',
                              python_callable=push_xcom_query,
                              op_kwargs={'dag_id': dag_id, 'postgres_conn_id': postgres_def_conn_id, # trying kwargs for research reason
                                         'schema_name': postgres_def_schema_name, 'table_name': table_name},
                              provide_context=True)
            >>PythonOperator(
                task_id='job_push_result_task',
                python_callable=push_xcom_end_job,
                provide_context=True)
            # >> BashOperator(
            #     task_id='test_jinja',
            #     bash_command='echo "This is run {{ run_id }} of task instance {{ ti }} "')
    )
    return contextdag


#dagarray = []
for dag_id in config:
    # print(dagname)
    # print(config.get(dagname))
    # dag_array.append(create_dag(dagname,config.get(dagname)))
    globals()[dag_id] = create_dag(dag_id, config.get(dag_id),default_args)


#Useless experiments
# dagname = 'abe_dag_id_1'
#dagconf = config.get(dag_id)
# with DAG(
#         dag_id=dagname,
#         default_args=dagconf,
#         dagrun_timeout=timedelta(minutes=60),
# ) as contextdag: (
#     BashOperator(
#         task_id='runme_' + dagname,
#         bash_command='echo "{{ task_instance_key_str }}" && sleep 1',
#     )
# )
