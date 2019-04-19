#importing module 
import sqlite3 
import pandas as pd
  
# connecting to the database  
connection = sqlite3.connect("incarceration.db") 
  
# cursor  
crsr = connection.cursor() 

# Add data to sqlite database
df = pd.read_csv('../data/incarceration_trends_w_percs.csv')

# SQL command to create a table in the database 
df.to_sql("incarceration", connection, if_exists="replace")

# Check to confirm all is working
sql_command = """SELECT *
FROM incarceration
WHERE county_name = 'Alameda County';
"""

# execute the statement 
crsr.execute(sql_command)

data = crsr.fetchone()

print(data)
  
# To save the changes in the files. Never skip this.  
# If we skip this, nothing will be saved in the database. 
connection.commit() 
  
# close the connection 
connection.close() 