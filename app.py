#!/usr/bin/env python3
from flask import Flask, render_template, request
import pandas as pd
from altair import Chart, X, Y, Axis, Data, DataFormat
import sqlite3

app = Flask(__name__)

# Declare global variable
county_list = []


# Index page
@app.route('/', methods=['POST'])
def index():
    county = request.form['county_name']
    county_list.append(county)

    return render_template('county_data.html')

### Altair Data Routes

WIDTH = 600
HEIGHT = 300

@app.route("/bar")
def data_bar():

    # Connect to database
    conn = sqlite3.connect('./db/incarceration.db')

    # Identify the requested county
    county_name = county_list.pop()

    #Query the database
    county_data = pd.read_sql_query(f"""SELECT *
                                    FROM incarceration
                                    WHERE county_name = '{county_name}';
                                    """, conn)

    # Close connection
    conn.close()

    # Create the chart
    chart = Chart(data=county_data, height=HEIGHT, width=WIDTH).mark_bar(color='lightgreen').encode(
        X('year:O', axis=Axis(title='Year')),
        Y('total_prison_pop', axis=Axis(title='Total Prison Population'))
    )
    return chart.to_json()

@app.route("/county")
def county():
    return render_template('county_form.html')

if __name__ == '__main__':
    app.run(debug=True)