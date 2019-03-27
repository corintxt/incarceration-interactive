from flask import Flask, render_template, request
import pandas as pd
from altair import Chart, X, Y, Axis, Data, DataFormat
import sqlite3

app = Flask(__name__)

# Connect to database
conn = sqlite3.connect('./db/incarceration.db')

# Filter database based on county selection
county_name = 'Alameda County'

county_data = pd.read_sql_query(f"""SELECT *
                                FROM incarceration
                                WHERE county_name = '{county_name}';
                                """, conn)

# Index page
@app.route('/', methods=['POST'])
def index():
    return render_template('county_data.html')

### Altair Data Routes

WIDTH = 600
HEIGHT = 300

@app.route("/bar")
def data_bar():

    #county_data = request.form['county_name']

    chart = Chart(data=county_data, height=HEIGHT, width=WIDTH).mark_bar(color='lightgreen').encode(
        X('year:O', axis=Axis(title='Year')),
        Y('total_prison_pop', axis=Axis(title='Total Prison Population'))
    )
    return chart.to_json()

@app.route("/county")
def county():
    return render_template('county_form.html')

if __name__ == '__main__':
    app.run(port=5000, debug=True)