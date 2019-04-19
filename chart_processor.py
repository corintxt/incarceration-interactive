import pandas as pd

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
    melt['demographic'] = melt.apply (lambda row: label_demographics(row), axis=1)

    return melt