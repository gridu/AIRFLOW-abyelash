from datetime import datetime
from datetime import timedelta
from airflow.models import DAG, Variable
from airflow.contrib.sensors.file_sensor import FileSensor
from airflow.operators.dagrun_operator import TriggerDagRunOperator
from airflow.operators.bash_operator import BashOperator
from airflow.sensors.external_task_sensor import ExternalTaskSensor
from airflow.operators.subdag_operator import SubDagOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
from os.path import dirname
from jobs_dag import config

default_args = {
   'owner': 'Airflow',
   'start_date': datetime(2020, 1, 1)
}
trigger_dir = dirname(Variable.get('name_path_variable', default_var= 'default value')+'/')
trigger_file = trigger_dir+'/runjobs'
#print(f'Wait for trigger file: {trigger_file}')

parent_dag = 'GRIDU_abe_trigger_dag'
#triggered_dag = 'abe_job_dag_id_3'
process_res_subdag = 'process_res_subdag'

def print_jobs_res(**context):
    for dag_id in config:
        result = context['ti'].xcom_pull(dag_id=dag_id, key ='job_result',  include_prior_dates=True)
        queryresult = context['ti'].xcom_pull(dag_id=dag_id, key ='query_result',  include_prior_dates=True)
        print(f'Result of {dag_id} is :: {result}')
        print(f'Result of QUERY is :: {queryresult}')

def load_subdag(parent_dag_name, child_dag_name, args):
    dag_subdag = DAG(
        dag_id='{0}.{1}'.format(parent_dag_name, child_dag_name),
        default_args=args,
        schedule_interval="@daily",
    )
    with dag_subdag:
        print_res_op = PythonOperator(task_id='print_result', python_callable=print_jobs_res, provide_context=True )
        for dag_id in config:
            ExternalTaskSensor(task_id='wait_' + dag_id, external_dag_id=dag_id, external_task_id=None).set_downstream(print_res_op)
        rm_run_file = BashOperator(task_id='remove_run_file', bash_command=f'echo Remove file {trigger_file} && rm {trigger_file}')
        finish_stamp = BashOperator(task_id='create_finished_timestamp', bash_command='touch '+trigger_dir+'/finished_{{ ts_nodash }}')  #Try format string and be amazed ! %)))
        print_res_op >> rm_run_file >> finish_stamp
    return dag_subdag


with DAG(
        dag_id=parent_dag,
        default_args=default_args,
        dagrun_timeout=timedelta(minutes=1),
        schedule_interval= None
    ) as contextdag:
            fs = FileSensor(
                task_id="file_sensor_task",
                poke_interval= 30,
                filepath=trigger_file)
            waitjobs = SubDagOperator(
                task_id=process_res_subdag,
                subdag=load_subdag(parent_dag,process_res_subdag,default_args))
            for dag_id in config:
                tr = TriggerDagRunOperator(
                    task_id="trigger_"+dag_id,
                    trigger_dag_id=dag_id,
                    execution_date='{{ execution_date }}')
                tr.set_upstream(fs)
                tr.set_downstream(waitjobs)

