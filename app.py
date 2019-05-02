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
    """Flattens list of lists returned by unpacking pandas series.values
    after SQL query"""
    flat_list = [item for sublist in series.values for item in sublist]
    return flat_list

# Function to avoid errors trying to round null data values for the multiline chart
def to_percentage(num):
    """
    Function to avoid errors trying to round null data values for the multiline chart.
    """
    if isinstance(num, float):
        num = num*100
        return round(num, 0)
    else:
        pass
    
### Routing stuff
# Index page
@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        conn = sqlite3.connect('./db/incarceration.db')
        
        population =  pd.read_sql_query(f"""SELECT year, total_pop, total_jail_pop, total_prison_pop
                                    FROM incarceration
                                    WHERE county_name = '{session.get('current_county')}'
                                    AND state = '{session.get('current_state')}'
                                    """, conn)
        # Determine if prison data exists
        prison_data = set(list(population.total_prison_pop))
        session['prison_data_exists']=(prison_data != {None})    

        # Get total population in year 2016
        total_pop = int(population[population.year==2016].total_pop)
        total_pop_formatted = "{:,}".format(total_pop)

        # get max jail population, and associated years
        max_jail_df = population.loc[population['total_jail_pop'].idxmax()]
        max_jail_pop = int(max_jail_df.total_jail_pop)
        max_jail_pop_formatted = "{:,}".format(max_jail_pop)
        max_jail_pop_year = int(max_jail_df.year)
        
        # get max prison population, and associated years if prison data exists
        if session.get('prison_data_exists'):
            max_prison_df = population.loc[population['total_prison_pop'].idxmax()]
            max_prison_pop = int(max_prison_df.total_prison_pop)
            max_prison_pop_formatted = "{:,}".format(max_prison_pop)
            max_prison_pop_year = int(max_prison_df.year)

        # get state population
        state_population =  pd.read_sql_query(f"""SELECT sum(total_pop)
                                    FROM incarceration
                                    WHERE state = '{session.get('current_state')}'
                                    AND year = '2016'
                                    """, conn)
        state_pop = state_population.values[0][0]
        state_pop_formatted = "{:,}".format(state_pop)


        facilities_data =  pd.read_sql_query(f"""SELECT num_facilites, capacity
                                    FROM incarceration
                                    WHERE county_name = '{session.get('current_county')}'
                                    AND state = '{session.get('current_state')}'
                                    AND year = '2016'
                                    """, conn)

        session['num_facilities'] = int(facilities_data['num_facilites'][0])
        session['capacity'] = int(facilities_data['capacity'][0])

        if session.get('prison_data_exists'):
            return render_template('county_data.html',
                                    total_population=total_pop_formatted, 
                                    state_pop=state_pop_formatted,
                                    max_jail_pop=max_jail_pop_formatted,
                                    max_jail_pop_year=max_jail_pop_year,
                                    max_prison_pop=max_prison_pop_formatted,
                                    max_prison_pop_year=max_prison_pop_year)
        else:
            return render_template('county_data.html',
                                total_population=total_pop_formatted, 
                                state_pop=state_pop_formatted,
                                max_jail_pop=max_jail_pop_formatted,
                                max_jail_pop_year=max_jail_pop_year)

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

@app.route("/bar_prison")
def data_bar_prison():
    county_data = read_county_from_db(session.get('current_state'), session.get('current_county'))

    # Create the chart
    chart = Chart(data=county_data, height=HEIGHT, width=WIDTH).mark_bar(color='#2f3142').encode(
        X('year:O', axis=Axis(title='Year')),
        Y('total_prison_pop', axis=Axis(title='Total Prison Population'))
    ).properties(
    title='Prison population in {}'.format(session.get('current_county'))
    )
    return chart.to_json()

@app.route("/bar_jail")
def data_bar_jail():
    county_data = read_county_from_db(session.get('current_state'), session.get('current_county'))

    # Create the chart
    jail = Chart(data=county_data, height=HEIGHT, width=WIDTH).mark_bar(color='#444760').encode(
        X('year:O', axis=Axis(title='Year')),
        Y('total_jail_pop', axis=Axis(title='Total Jail Population')),
        tooltip=[alt.Tooltip('year', title='Year'), alt.Tooltip('total_jail_pop', title='Total jail population')]
    ).properties(
    title='Jail population in {}'.format(session.get('current_county'))
    ).interactive()

    pre_trial = Chart(data=county_data, height=HEIGHT, width=WIDTH).mark_bar(
        color="#d66241", interpolate='step-after', line=True,
        ).encode(
        X('year:O', axis=Axis(title='Year')),
        Y('total_jail_pretrial', axis=Axis(title='Number of inmates')),
        tooltip=[alt.Tooltip('year', title='Year'), alt.Tooltip('total_jail_pretrial', title='Pre-trial jail population')]        
    ).properties(
    title='Pre-trial jail population in {}'.format(session.get('current_county'))
    ).interactive()

    chart = alt.layer(jail + pre_trial)

    return chart.to_json()

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
               'Total black population (15-64)',
               'White jail population',
               'Black jail population',
               'White prison population',
               'Black prison population']

    # Define color pairs matched to above demographics
    hex_colors = ['#cccec1',
                '#272727',
                '#cccec1',
                '#272727',
                '#cccec1',
                '#272727']

    # Combine demographic and colors into a dictionary
    demographic_labels = dict(zip(demographics, hex_colors))

    # Create pairs of variables to be used in the stacked charts
    wb_general = ['perc_white_total_pop', 'perc_black_total_pop']
    wb_jail = ['perc_white_jail_pop', 'perc_black_jail_pop']
    wb_prison = ['perc_white_prison_pop', 'perc_black_prison_pop']

    # General population chart
    total_wb_population = alt.Chart(source[source['variable'].isin(wb_general)], height=150, width=500).mark_bar().encode(
    x=alt.X("year:O", axis=Axis(title='Year')),
    y=alt.Y("value:Q", stack="normalize", axis=Axis(title='Ratio')),
    color=alt.Color('demographic:N', legend=None,
             scale=alt.Scale(domain=list(demographic_labels.keys()),
                            range=list(demographic_labels.values())
                            )
             )
    ).properties(
        title='Ratio of white/black residents in total county population (15-64)'
    )

    # White/black jail population chart
    total_wb_jail = alt.Chart(source[source['variable'].isin(wb_jail)], height=150, width=500).mark_bar().encode(
    x=alt.X("year:O", axis=Axis(title='Year')),
    y=alt.Y("value:Q", stack="normalize", axis=Axis(title='Ratio')),
    color=alt.Color('demographic:N', legend=None,
             scale=alt.Scale(domain=list(demographic_labels.keys()),
                            range=list(demographic_labels.values())
                            )
             )
    ).properties(
        title='Ratio of white/black  inmates in jail population'
    )

    if session.get('prison_data_exists'):
        total_wb_prison = alt.Chart(source[source['variable'].isin(wb_prison)], height=150, width=500).mark_bar().encode(
        x=alt.X("year:O", axis=Axis(title='Year')),
        y=alt.Y("value:Q", stack="normalize", axis=Axis(title='Ratio')),
        color=alt.Color('demographic:N', legend=None,
                scale=alt.Scale(domain=list(demographic_labels.keys()),
                                range=list(demographic_labels.values())
                                )
                )
        ).properties(
            title='Ratio of white/black  inmates in prison population'
        )

        # Concatenate charts
        chart = alt.vconcat(total_wb_population, total_wb_jail, total_wb_prison)
    else:
        # Concatenate charts
        chart = alt.vconcat(total_wb_population, total_wb_jail)

    return chart.to_json()    


@app.route("/crime")
def crime():
    county_data = read_county_from_db(session.get('current_state'), session.get('current_county'))

    source = chart_processor.process_crime(county_data)

    chart = alt.Chart(source, width=WIDTH, height=HEIGHT).mark_circle(
                        opacity=0.7,
                        stroke='grey',
                        strokeWidth=1
                    ).encode(
                        alt.X('year:O', axis=alt.Axis(labelAngle=0, title='Year')),
                        alt.Y('Crime:N'),
                        alt.Size('Number:Q',
                            scale=alt.Scale(range=[0, 1500]), 
                            legend=alt.Legend(title='Reports')
                        ),
                        alt.Color('Crime:N', legend=None)
                    ).properties(
                        title='Reported crime by type'
                    )
    
    return chart.to_json()




# Called below in `scatter` route
def test_nulls_for_year(year, state, conn):
    percent_nulls = pd.read_sql_query(f"""SELECT
                                   100.0 * count(total_prison_pop) / count(1) as PercentNotNull
                                FROM
                                   incarceration
                                WHERE state = '{state}'
                                AND year = {year};
                                """, conn)
    return percent_nulls


@app.route("/scatter")
def county_scatter():
    state_name = session.get('current_state')
    county_name = session.get('current_county')
        
    #Connect to the database
    conn = sqlite3.connect('./db/incarceration.db')

    # Determine whether 2015 or 2016 has more data
    year_2016_nulls = test_nulls_for_year(2016, state_name, conn)

    year_2015_nulls = test_nulls_for_year(2015, state_name, conn)

    year = 2016 # default year

    # Test to see if 2015 has more non-null values
    if year_2016_nulls.iloc[0]['PercentNotNull'] < year_2015_nulls.iloc[0]['PercentNotNull']:
            year = 2015
        
    # Select prison population data for the entire state for the selected year
    all_counties_prison_pop = pd.read_sql_query(f"""SELECT county_name, total_pop, total_prison_pop, urbanicity
                                    FROM
                                    incarceration
                                    WHERE state = '{state_name}'
                                    AND year = {year};
                                    """, conn)

    # Select prison population data for the specific county for the selected year
    county_prison_pop = pd.read_sql_query(f"""SELECT county_name, total_pop, total_prison_pop, urbanicity
                                    FROM
                                    incarceration
                                    WHERE state = '{state_name}'
                                    AND county_name = '{county_name}'
                                    AND year = {year};
                                    """, conn)
        
    # Close connection
    conn.close()

    state_chart = Chart(data=all_counties_prison_pop, height=HEIGHT, width=WIDTH).mark_circle(size=70).encode(
        X('total_pop', axis=Axis(title='County population')),
        Y('total_prison_pop', axis=Axis(title='Total prison population')),
        color=alt.Color('urbanicity', legend=alt.Legend(title='Urbanicity')),
        size=alt.Color('total_pop', legend=alt.Legend(title='Total population')),
        tooltip=[alt.Tooltip('county_name', title='County'), alt.Tooltip('total_pop', title='Total county population'), alt.Tooltip('total_prison_pop', title='Total prison population')],
    ).properties(
    title='Statewide prison population {}, {}'.format(year, state_name)).interactive()

    county_chart = Chart(data=county_prison_pop, height=HEIGHT, width=WIDTH).mark_square(
        size=250, fillOpacity=0.5, stroke='black', color='black').encode(
        X('total_pop', axis=Axis(title='County population')),
        Y('total_prison_pop', axis=Axis(title='Total prison population')),
        tooltip=['county_name', 'total_pop', 'total_prison_pop']
    ).interactive()

    chart = alt.layer(county_chart, state_chart)

    return chart.to_json()

@app.route("/pretrial")
def pretrial_jail_chart():
    county_data = read_county_from_db(session.get('current_state'), session.get('current_county'))

    chart = Chart(data=county_data, height=HEIGHT, width=WIDTH).mark_line(
        color="#08080B",
        interpolate='step-after',
        line=True,
        ).encode(
        X('year:O', axis=Axis(title='Year')),
        Y('total_jail_pretrial', axis=Axis(title='Number of inmates')),
        tooltip=['year', 'total_jail_pretrial']        
    ).properties(
    title='Pre-trial jail population in {}'.format(session.get('current_county'))
    ).interactive()
    return chart.to_json()

@app.route("/map")
def draw_map():
    fips = session.get('fips')
    state_id = int(str(fips)[0:-3])

    states_topo = alt.topo_feature('https://raw.githubusercontent.com/vega/vega-datasets/master/data/us-10m.json', feature='states')
    counties_topo = alt.topo_feature('https://raw.githubusercontent.com/vega/vega-datasets/master/data/us-10m.json', feature='counties')

    state_map = Chart(data=states_topo, height=HEIGHT, width=WIDTH).mark_geoshape(
                fill='#827f7f',
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