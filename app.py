#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import altair as alt
from altair import Chart, X, Y, Axis, Data, DataFormat
import sqlite3

app = Flask(__name__)

def read_county_from_db(state_name, county_name):
    # Connect to database
    conn = sqlite3.connect('./db/incarceration.db')

    #Query the database
    data =  pd.read_sql_query(f"""SELECT *
                                    FROM incarceration
                                    WHERE county_name = '{county_name}'
                                    AND state = '{state_name}';
                                    """, conn)
    
    # Close connection
    conn.close()

    return data


def flatten(series):
    '''Flattens list of lists returned by unpacking pandas series.values
    after SQL query'''
    flat_list = [item for sublist in series.values for item in sublist]
    return flat_list
    

### Routing stuff
# Index page
@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        conn = sqlite3.connect('./db/incarceration.db')
        
        population =  pd.read_sql_query(f"""SELECT total_pop, total_jail_pop, total_prison_pop
                                    FROM incarceration
                                    WHERE county_name = '{session.get('current_county')}'
                                    AND state = '{session.get('current_state')}'
                                    AND year = 2016;
                                    """, conn)

        total_pop = "{:,}".format(flatten(population)[0])

        return render_template('county_data.html', total_population=total_pop)

    # Redirect any GET request on '/' to county select
    else:
        return redirect(url_for('select'))

# Select
@app.route('/select')
def select():
    # Connect to database
    conn = sqlite3.connect('./db/incarceration.db')

    # Query the database
    state_data =  pd.read_sql_query(f"""SELECT DISTINCT state 
                                    FROM incarceration;
                                    """, conn)

    states = flatten(state_data)
    
    conn.close()

    session['states'] = states

    return render_template('select.html', states=states)

@app.route('/select/<state_name>/')
def show_state(state_name):
    # Connect to database
    conn = sqlite3.connect('./db/incarceration.db')

    # Query the database
    county_data =  pd.read_sql_query(f"""SELECT DISTINCT county_name 
                                    FROM incarceration
                                    WHERE state = '{state_name}';
                                    """, conn)

    counties = flatten(county_data)
    
    conn.close()

    session['counties'] = counties

    return render_template('select.html', state_name=state_name, counties=counties, states=session.get('states'))

@app.route('/select/<state_name>/<county_name>')
def show_county(state_name, county_name):
    session['current_county'] = county_name
    session['current_state'] = state_name

    conn = sqlite3.connect('./db/incarceration.db')

    fips = pd.read_sql_query(f"""SELECT DISTINCT fips 
                                    FROM incarceration
                                    WHERE state = '{state_name}'
                                    AND county_name = '{county_name}';
                                    """, conn)

    conn.close()

    session['fips'] = str(fips.values[0][0]) #unpack list of lists

    return render_template('select.html', state_name=state_name, county_name=county_name,
                            counties=session.get('counties'), states=session.get('states'))

# Select county form
@app.route("/county")
def county():
    return render_template('county_form.html')


### Altair data routes
WIDTH = 600
HEIGHT = 300

@app.route("/bar")
def data_bar():
    county_data = read_county_from_db(session.get('current_state'), session.get('current_county'))

    # Create the chart
    chart = Chart(data=county_data, height=HEIGHT, width=WIDTH).mark_bar(color='lightgreen').encode(
        X('year:O', axis=Axis(title='Year')),
        Y('total_prison_pop', axis=Axis(title='Total Prison Population'))
    ).properties(
    title='Prison population in {}'.format(session.get('current_county'))
    )
    return chart.to_json()

@app.route("/pretrial")
def pretrial_jail_chart():
    county_data = read_county_from_db(session.get('current_state'), session.get('current_county'))

    chart = Chart(data=county_data, height=HEIGHT, width=WIDTH).mark_area(color='lightblue').encode(
        X('year:O', axis=Axis(title='Year')),
        Y('total_jail_pretrial', axis=Axis(title='Number of inmates'))
    ).properties(
    title='Pre-trial jail population in {}'.format(session.get('current_county'))
    )
    return chart.to_json()

@app.route("/map")
def draw_map():
    fips = session.get('fips')
    state_id = int(str(fips)[0:-3])

    states_topo = alt.topo_feature('https://raw.githubusercontent.com/vega/vega-datasets/master/data/us-10m.json', feature='states')
    counties_topo = alt.topo_feature('https://raw.githubusercontent.com/vega/vega-datasets/master/data/us-10m.json', feature='counties')


    state_map = Chart(data=states_topo, height=HEIGHT, width=WIDTH).mark_geoshape(
                fill='lightgrey',
                stroke='white'
            ).transform_filter((alt.datum.id == state_id))

    county_map = Chart(data=counties_topo, height=HEIGHT, width=WIDTH).mark_geoshape(
                fill='red',
                stroke='white'
            ).transform_filter((alt.datum.id == int(fips)))

    chart = alt.layer(state_map, county_map)
    
    return chart.to_json()

if __name__ == '__main__':
    app.secret_key = 'very secret key' #Fix this later!
    app.run(debug=True)