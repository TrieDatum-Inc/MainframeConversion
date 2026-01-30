"""
Airflow DAG for CBTRN02C - Post Daily Transactions

This DAG schedules the daily transaction posting job on Databricks,
replicating the mainframe JCL job POSTTRAN.jcl.

Mainframe Schedule: Typically runs daily after business hours
Databricks Schedule: Daily at 11:00 PM UTC (configurable)

DAG Flow:
1. Check for new DALYTRAN file in landing zone
2. Ingest EBCDIC file to bronze Delta table
3. Run CBTRN02C job to post transactions
4. Generate reconciliation report
5. Send notification on completion/failure

Prerequisites:
- Databricks workspace with Unity Catalog
- Databricks connection configured in Airflow
- Landing zone path configured for DALYTRAN files
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator
from airflow.operators.email import EmailOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.trigger_rule import TriggerRule
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# DAG Configuration
# =============================================================================

# Default arguments for all tasks
default_args = {
    'owner': 'carddemo-batch',
    'depends_on_past': False,
    'email': ['batch-alerts@company.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=2),
}

# Databricks configuration
DATABRICKS_CONN_ID = 'databricks_default'
DATABRICKS_CLUSTER_ID = '{{ var.value.databricks_cluster_id }}'  # From Airflow Variables

# Unity Catalog configuration
CATALOG = 'carddemo'
BRONZE_SCHEMA = 'bronze'
SILVER_SCHEMA = 'silver'

# File paths
LANDING_ZONE_PATH = '/mnt/landing/dalytran/'
ARCHIVE_PATH = '/mnt/archive/dalytran/'

# =============================================================================
# Task Functions
# =============================================================================

def check_for_dalytran_file(**context):
    """
    Check if a new DALYTRAN file exists in the landing zone.
    Returns the task to branch to based on file existence.
    """
    from airflow.providers.databricks.hooks.databricks import DatabricksHook
    
    execution_date = context['execution_date']
    file_date = execution_date.strftime('%Y%m%d')
    expected_file = f"{LANDING_ZONE_PATH}DALYTRAN.{file_date}"
    
    logger.info(f"Checking for file: {expected_file}")
    
    # In production, use Databricks DBFS API or cloud storage API to check
    # For now, we assume file exists and proceed
    # hook = DatabricksHook(databricks_conn_id=DATABRICKS_CONN_ID)
    
    # Simulate file check - in production, implement actual check
    file_exists = True  # Replace with actual check
    
    if file_exists:
        logger.info(f"File found: {expected_file}")
        return 'ingest_dalytran'
    else:
        logger.warning(f"File not found: {expected_file}")
        return 'no_file_to_process'


def generate_batch_id(**context):
    """
    Generate a unique batch ID for this run.
    Used for idempotency and reconciliation.
    """
    execution_date = context['execution_date']
    batch_id = execution_date.strftime('%Y%m%d%H%M%S')
    
    # Push to XCom for downstream tasks
    context['ti'].xcom_push(key='batch_id', value=batch_id)
    logger.info(f"Generated batch_id: {batch_id}")
    
    return batch_id


def validate_reconciliation(**context):
    """
    Validate the reconciliation report from CBTRN02C.
    Compare counts to ensure data integrity.
    """
    ti = context['ti']
    
    # Get job output from XCom (pushed by Databricks task)
    job_output = ti.xcom_pull(task_ids='run_cbtrn02c', key='return_value')
    
    if job_output:
        records_read = job_output.get('records_read', 0)
        records_written = job_output.get('records_written', 0)
        records_rejected = job_output.get('records_rejected', 0)
        
        # Validate counts balance
        if records_read != records_written + records_rejected:
            raise ValueError(
                f"Reconciliation failed: {records_read} read != "
                f"{records_written} written + {records_rejected} rejected"
            )
        
        logger.info(f"Reconciliation passed: {records_read} records processed")
        return True
    else:
        logger.warning("No job output received for reconciliation")
        return False


# =============================================================================
# Databricks Job Configurations
# =============================================================================

# Notebook task for ingesting EBCDIC file to bronze table
ingest_notebook_task = {
    'notebook_task': {
        'notebook_path': '/Repos/carddemo/databricks-migration/notebooks/ingest_dalytran',
        'base_parameters': {
            'landing_zone_path': LANDING_ZONE_PATH,
            'catalog': CATALOG,
            'schema': BRONZE_SCHEMA,
            'batch_id': '{{ ti.xcom_pull(task_ids="generate_batch_id", key="batch_id") }}'
        }
    },
    'existing_cluster_id': DATABRICKS_CLUSTER_ID
}

# Python task for running CBTRN02C
cbtrn02c_python_task = {
    'spark_python_task': {
        'python_file': 'dbfs:/jobs/cbtrn02c/post_daily_transactions.py',
        'parameters': [
            '--catalog', CATALOG,
            '--schema', SILVER_SCHEMA,
            '--batch_id', '{{ ti.xcom_pull(task_ids="generate_batch_id", key="batch_id") }}'
        ]
    },
    'existing_cluster_id': DATABRICKS_CLUSTER_ID
}

# Alternative: Use Databricks Jobs (pre-configured job)
# This is the recommended approach for production
CBTRN02C_JOB_ID = '{{ var.value.cbtrn02c_job_id }}'  # From Airflow Variables


# =============================================================================
# DAG Definition
# =============================================================================

with DAG(
    dag_id='carddemo_cbtrn02c_post_daily_transactions',
    default_args=default_args,
    description='Post daily transactions - migrated from mainframe CBTRN02C/POSTTRAN.jcl',
    schedule_interval='0 23 * * *',  # Daily at 11 PM UTC
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['carddemo', 'batch', 'transactions', 'mainframe-migration'],
    doc_md=__doc__,
) as dag:
    
    # Task 1: Generate batch ID for this run
    generate_batch_id_task = PythonOperator(
        task_id='generate_batch_id',
        python_callable=generate_batch_id,
        provide_context=True,
    )
    
    # Task 2: Check for DALYTRAN file
    check_file_task = BranchPythonOperator(
        task_id='check_for_dalytran_file',
        python_callable=check_for_dalytran_file,
        provide_context=True,
    )
    
    # Task 3a: No file to process (skip path)
    no_file_task = EmptyOperator(
        task_id='no_file_to_process',
    )
    
    # Task 3b: Ingest DALYTRAN file to bronze table
    ingest_task = DatabricksSubmitRunOperator(
        task_id='ingest_dalytran',
        databricks_conn_id=DATABRICKS_CONN_ID,
        json=ingest_notebook_task,
    )
    
    # Task 4: Run CBTRN02C job
    # Option A: Submit as a new run
    run_cbtrn02c_task = DatabricksSubmitRunOperator(
        task_id='run_cbtrn02c',
        databricks_conn_id=DATABRICKS_CONN_ID,
        json=cbtrn02c_python_task,
    )
    
    # Option B: Trigger pre-configured Databricks Job (recommended for production)
    # run_cbtrn02c_task = DatabricksRunNowOperator(
    #     task_id='run_cbtrn02c',
    #     databricks_conn_id=DATABRICKS_CONN_ID,
    #     job_id=CBTRN02C_JOB_ID,
    #     notebook_params={
    #         'batch_id': '{{ ti.xcom_pull(task_ids="generate_batch_id", key="batch_id") }}'
    #     }
    # )
    
    # Task 5: Validate reconciliation
    validate_task = PythonOperator(
        task_id='validate_reconciliation',
        python_callable=validate_reconciliation,
        provide_context=True,
    )
    
    # Task 6: Send success notification
    success_notification = EmailOperator(
        task_id='send_success_notification',
        to=['batch-alerts@company.com'],
        subject='CBTRN02C Completed Successfully - {{ ds }}',
        html_content="""
        <h2>CBTRN02C - Post Daily Transactions</h2>
        <p>Job completed successfully for {{ ds }}</p>
        <p>Batch ID: {{ ti.xcom_pull(task_ids="generate_batch_id", key="batch_id") }}</p>
        <p>Check Databricks for detailed reconciliation report.</p>
        """,
        trigger_rule=TriggerRule.ALL_SUCCESS,
    )
    
    # Task 7: Send failure notification
    failure_notification = EmailOperator(
        task_id='send_failure_notification',
        to=['batch-alerts@company.com'],
        subject='CBTRN02C FAILED - {{ ds }}',
        html_content="""
        <h2>CBTRN02C - Post Daily Transactions FAILED</h2>
        <p>Job failed for {{ ds }}</p>
        <p>Batch ID: {{ ti.xcom_pull(task_ids="generate_batch_id", key="batch_id") }}</p>
        <p>Please investigate immediately.</p>
        """,
        trigger_rule=TriggerRule.ONE_FAILED,
    )
    
    # Task 8: End task (join point)
    end_task = EmptyOperator(
        task_id='end',
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    )
    
    # =============================================================================
    # Task Dependencies
    # =============================================================================
    
    # Main flow
    generate_batch_id_task >> check_file_task
    
    # Branch: File exists
    check_file_task >> ingest_task >> run_cbtrn02c_task >> validate_task >> success_notification >> end_task
    
    # Branch: No file
    check_file_task >> no_file_task >> end_task
    
    # Failure notification (triggered on any failure)
    [ingest_task, run_cbtrn02c_task, validate_task] >> failure_notification


# =============================================================================
# Additional DAGs for related batch jobs
# =============================================================================

# You can create similar DAGs for:
# - INTCALC (Interest Calculation) - runs end of cycle
# - CREASTMT (Statement Generation) - runs monthly
# - TRANREPT (Transaction Report) - runs daily after CBTRN02C

# Example: Monthly batch orchestration DAG
# with DAG(
#     dag_id='carddemo_monthly_batch',
#     schedule_interval='0 2 1 * *',  # 2 AM on 1st of month
#     ...
# ) as monthly_dag:
#     # Run interest calculation
#     # Generate statements
#     # Archive old transactions
