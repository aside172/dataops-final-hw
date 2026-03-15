from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator


def report() -> None:
    print("DataOps homework DAG executed successfully")


with DAG(
    dag_id="hello_dataops",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["homework", "dataops"],
) as dag:
    PythonOperator(task_id="report_status", python_callable=report)
