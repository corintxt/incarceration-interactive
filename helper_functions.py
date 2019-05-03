import pandas as pd

## PRISON DEMOGRPAHIC PROCESSING
# List the values we are interested in 
values = ['perc_white_total_pop',
        'perc_white_prison_pop',
        'perc_white_jail_pop',
        'perc_black_total_pop',
        'perc_black_prison_pop',
        'perc_black_jail_pop']

# Function to reformat race demographic labels
def label_demographics(row):
    if row['variable'] == 'perc_white_total_pop':
        return 'Total white population (15-64)'
    if row['variable'] == 'perc_white_prison_pop':
        return 'White prison population'
    if row['variable'] == 'perc_white_jail_pop':
        return 'White jail population'
    if row['variable'] == 'perc_black_total_pop':
        return 'Total black population (15-64)'
    if row['variable'] == 'perc_black_prison_pop':
        return 'Black prison population'
    if row['variable'] == 'perc_black_jail_pop':
        return 'Black jail population'

def process_data(dataframe):
    melt = pd.melt(dataframe, id_vars=['year'], 
                       value_vars=values)

    # Create a new column with a lambda function
    melt['demographic'] = melt.apply(lambda row: label_demographics(row), axis=1)

    return melt


## CRIME DEMOGRAPHIC PROCESSING
crimes = [
    'violent_crime',
    'property_crime',
    'murder_crime',
    'robbery_crime',
    'agr_assault_crime',
    'burglary_crime',
    'larceny_crime',
    'mv_theft_crime',
    'arson_crime'
]

# Reformat crime labels
def label_crimes(row):
    if row['Crime'] == 'violent_crime':
        return 'Violent crime'
    if row['Crime'] == 'property_crime':
        return 'Property crime'
    if row['Crime'] == 'murder_crime':
        return 'Murder'
    if row['Crime'] == 'robbery_crime':
        return 'Robbery'
    if row['Crime'] == 'agr_assault_crime':
        return 'Aggravated assault'
    if row['Crime'] == 'burglary_crime':
        return 'Burglary'
    if row['Crime'] == 'larceny_crime':
        return 'Larceny'
    if row['Crime'] == 'mv_theft_crime':
        return 'Motor vehicle theft'
    if row['Crime'] == 'arson_crime':
        return 'Arson'

def process_crime(dataframe):
    melt = pd.melt(dataframe, 
                       id_vars=['year'], 
                       value_vars=crimes, 
                       var_name='Crime', 
                       value_name='Number')

    melt['Crime'] = melt.apply (lambda row: label_crimes(row), axis=1) 

    return melt

## MISC HELPER FUNCTIONS
def read_county_from_db(state_name, county_name):
    """
    Connects to the database and returns a DataFrame of all data for specific county
    """
    # Connect to database
    conn = sqlite3.connect('./db/incarceration.db')

    # Query the database
    data = pd.read_sql_query(f"""SELECT *
                                    FROM incarceration
                                    WHERE county_name = '{county_name}'
                                    AND state = '{state_name}';
                                    """, conn)

    # Close connection
    conn.close()

    return data


def flatten(series):
    """
    Flattens list of lists returned by unpacking pandas series.values
    after SQL query
    """
    flat_list = [item for sublist in series.values for item in sublist]
    return flat_list

def to_percentage(num):
    """
    Function to avoid errors trying to round null data values for the multiline chart.
    """
    if isinstance(num, float):
        num = num*100
        return round(num, 0)
    else:
        pass

