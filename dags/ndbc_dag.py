import pandas as pd
import requests
from airflow.utils.dates import days_ago
from airflow.models import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta
from airflow.hooks.postgres_hook import PostgresHook



data_path = 'https://www.ndbc.noaa.gov/data/realtime2/51001.spec'

def check_for_file():
	request = requests.head(data_path)
	if request.status_code == 200:
	     print('file exists')
	else:
	    print('file does not exist')
	return "OK"

def clean_load_data():
	missing_values = ["MM"]
	df = pd.read_csv(data_path,
		sep = '\s+',
		parse_dates = True,
		skiprows = [1],
		na_values = missing_values)
	#df["DATE"] = df["#YY"].astype(str)+'/'+df["MM"].astype(str)+'/'+df["DD"].astype(str)+'/'+df["hh"].astype(str)+'/'+df["mm"].astype(str)
	pg_hook = PostgresHook(postgres_conn_id='NDBC_51001')
	
	#sample_date = df["DATE"] 
	significant_wave_height = df["WVHT"][0]
	swell_height = df["SwH"][0]
	swell_period = df["SwP"][0]
	wind_wave_height = df["WWH"][0]
	wind_wave_period = df["WWP"][0]
	#swell_direction = df["SwD"]
	#wind_wave_direction = df["WWD"]
	#steepness = df["STEEPNESS"]
	average_period = df["APD"][0]
	#dominant_period_wave_direction = ["MWD"]

	row = (significant_wave_height, swell_height, swell_period,
	 wind_wave_height, wind_wave_period, average_period)

	insert_cmd = """INSERT INTO Detailed_Wave_Data_Table (significant_wave_height, swell_height, swell_period,
	 wind_wave_height, wind_wave_period, average_period) VALUES (%s, %s, %s, %s, %s, %s);"""

	pg_hook.run(insert_cmd, parameters=row)

DEFAULT_ARGS = {
    'owner': 'chris',
    'depends_on_past': False,
    'schedule_interval': '@hourly',
    'email': ['holloway.christopher.t@gmail.com'],
    'email_on_failure': False,
    'email_on_retry': False 
}
with DAG(
	dag_id ='NDBC_51001',
	default_args = DEFAULT_ARGS,
	dagrun_timeout = timedelta(hours=1),
	start_date = days_ago(2)
) as dag:
	t1 = PythonOperator(
		task_id = 'file_check',
		python_callable = check_for_file,
		dag = dag
	)
	t2 = PythonOperator(
		task_id = 'clean_and_load',
		python_callable = clean_load_data,
		dag = dag
	)
	t1 >> t2