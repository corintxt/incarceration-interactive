#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
from altair import Chart, X, Y, Axis, Data, DataFormat
import sqlite3

app = Flask(__name__)

### Database stuff
# Declare global variable
county_list = []

def read_county_from_db(county_name):
    # Connect to database
    conn = sqlite3.connect('./db/incarceration.db')

    #Query the database
    data =  pd.read_sql_query(f"""SELECT *
                                    FROM incarceration
                                    WHERE county_name = '{county_name}';
                                    """, conn)
    
    # Close connection
    conn.close()

    return data

### Routing stuff
# Index page
@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        county = request.form['county_name']
        county_list.append(county)

        return render_template('county_data.html')

    # Redirect any GET request on '/' to county select
    else:
        return redirect(url_for('county'))

# Select county form
@app.route("/county")
def county():
    return render_template('county_form.html')


### Altair data Routes

WIDTH = 600
HEIGHT = 300

@app.route("/bar")
def data_bar():
    county_data = read_county_from_db(county_list.pop())

    # Create the chart
    chart = Chart(data=county_data, height=HEIGHT, width=WIDTH).mark_bar(color='lightgreen').encode(
        X('year:O', axis=Axis(title='Year')),
        Y('total_prison_pop', axis=Axis(title='Total Prison Population'))
    )
    return chart.to_json()

if __name__ == '__main__':
    app.run(debug=True)