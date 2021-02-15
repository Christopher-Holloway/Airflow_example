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
	""" Function to check if the data exists. Sometimes the buoys
	go offline, and do not report realtime data therefore no file is uploaded."""
	
	request = requests.head(data_path)
	if request.status_code == 200:
	     print('file exists')
	else:
	    print('file does not exist')
	return "OK"

def clean_load_data():
	""" Function to Extract the data into a Pandas dataframe, transform and
	and load into an existing Postgresql database."""

#Connect to database using the conn_id given in the Airflow Webserver

	pg_hook = PostgresHook(postgres_conn_id='NDBC_51001')

#NDBC documentation notes that missing values are expressed as "MM"	

	missing_values = ["MM"] 

#Extract the detailed wave summary data into Pandas dataframe

	df = pd.read_csv(data_path, 
		sep = '\s+',
		parse_dates = True,
		skiprows = [1],
		na_values = missing_values)
	
#Create a new column to simplify the sample date data

	#df["DATE"] = df["#YY"].astype(str)+'/'+df["MM"].astype(str)+'/'+df["DD"].astype(str)+'/'+df["hh"].astype(str)+'/'+df["mm"].astype(str)

#Create variables to input into the existing database

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

#Create a tuple for the data field values

	row = (significant_wave_height, swell_height, swell_period,
	 wind_wave_height, wind_wave_period, average_period)

#Create a sql command to load the data into the exisiting table

	insert_cmd = """INSERT INTO Detailed_Wave_Data_Table (significant_wave_height, swell_height, swell_period,
	 wind_wave_height, wind_wave_period, average_period) VALUES (%s, %s, %s, %s, %s, %s);"""

#Insert the data into the database

	pg_hook.run(insert_cmd, parameters=row)

#Define the default parameters for the Airflow Dag
DEFAULT_ARGS = {
    'owner': 'chris',
    'depends_on_past': False,
    'email': ['holloway.christopher.t@gmail.com'],
    'email_on_failure': False,
    'email_on_retry': False, 
}

#Define the dag, and its associated tasks

with DAG(
	dag_id ='NDBC_51001',
	schedule_interval="@hourly",
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