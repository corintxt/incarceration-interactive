#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import altair as alt
from altair import Chart, X, Y, Axis, Data, DataFormat
import sqlite3
import chart_processor

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

# Function to avoid errors trying to round null data values for the multiline chart
def to_percentage(num):
    if isinstance(num, float):
        num = num*100
        return round(num, 0)
    else:
        pass

@app.route("/multiline")
def multiline():
    county_data = read_county_from_db(session.get('current_state'), session.get('current_county'))

    source = chart_processor.process_data(county_data)

    # Create a column for the label
    source['value_label'] = source['value'].apply(lambda x: to_percentage(x))

    # Create a selection that chooses the nearest point & selects based on x-value
    nearest = alt.selection(type='single', nearest=True, on='mouseover',
                            fields=['year'], empty='none')


    demographics = ['Total white population (15-64)',
               'White prison population',
               'White jail population',
               'Total black population (15-64)',
               'Black prison population',
               'Black jail population']

    # Define color scheme blues and reds
    hex_colors = ['#2720e3',
                '#58d8f0',
                '#18a8c0',
                '#db3232',
                '#cc7777',
                '#ff9000']

    # Combine demographic and colors into a dictionary
    demographic_labels = dict(zip(demographics, hex_colors))

    # The basic line
    line = alt.Chart().mark_line(interpolate='basis').encode(
        x=alt.X('year:O', axis=alt.Axis(title='Year')),
        y=alt.Y('value:Q', axis=alt.Axis(format='%', title='Population')),
        color=alt.Color('demographic',
                scale=alt.Scale(domain=list(demographic_labels.keys()),
                                range=list(demographic_labels.values())
                                )
                ),
    )

    # Transparent selectors across the chart. This is what tells us
    # the x-value of the cursor
    selectors = alt.Chart().mark_point().encode(
        x='year:O',
        opacity=alt.value(0),
    ).add_selection(
        nearest
    )

    # Draw points on the line, and highlight based on selection
    points = line.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )

    # Draw text labels near the points, and highlight based on selection
    text = line.mark_text(align='left', dx=5, dy=-5).encode(
        text=alt.condition(nearest, 'value_label:Q', alt.value(' '))
    )

    # Draw a rule at the location of the selection
    rules = alt.Chart().mark_rule(color='gray').encode(
        x='year:O',
    ).transform_filter(
        nearest
    )

    # Put the five layers into a chart and bind the data
    chart = alt.layer(line, selectors, points, rules, text,
            data=source, width=600, height=300)
    
    return chart.to_json()


@app.route("/scatter")
def county_scatter():


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

    chart = alt.layer(state_map, county_map).configure_view(strokeWidth=0)
    
    return chart.to_json()

if __name__ == '__main__':
    app.secret_key = 'very secret key' #Fix this later!
    app.run(debug=True)