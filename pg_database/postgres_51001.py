from sqlalchemy import create_engine
from sqlalchemy_utils  import database_exists, create_database
import psycopg2

def make_database():
	"""
	Make Postgres database and create the table
	"""

	dbname = 'NDBC_51001DB'
	username = 'chrisholloway'
	tablename = 'Detailed_Wave_Data_Table'

	engine = create_engine('postgresql+psycopg2://%s@localhost/%s'%(username,dbname))

	if not database_exists(engine.url):
		create_database(engine.url)
	conn = psycopg2.connect(database = dbname, user = username)

	curr = conn.cursor()

	create_table = """CREATE TABLE  IF NOT EXISTS %s
				(
					sample_date						REAL,
					significant_wave_height			REAL,
					swell_height					REAL,
					swell_period					REAL,
					wind_wave_height				REAL,
					wind_wave_period				REAL,
					swell_direction					TEXT,
					wind_wave_direction				TEXT,
					steepness						REAL,
					average_period					REAL,
					dominant_period_wave_direction	REAL
				)
				""" % tablename
	curr.execute(create_table)
	conn.commit()
	conn.close()

if __name__ == "__main__":
	make_database()