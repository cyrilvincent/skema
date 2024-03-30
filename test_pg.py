import psycopg2
import config

connection = psycopg2.connect(config.connection_string)
c = connection.cursor()
sql = "ALTER TABLE public.sae0 ADD titi FLOAT"
c.execute(sql)
#print(c.fetchone())
connection.commit()

