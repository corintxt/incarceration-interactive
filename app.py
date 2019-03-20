from flask import Flask, render_template, request
import pandas as pd
from altair import Chart, X, Y, Axis, Data, DataFormat

app = Flask(__name__)


# Index page
@app.route('/')
def index():
    return render_template('main.html')


### Altair Data Routes

WIDTH = 600
HEIGHT = 300

alameda = pd.read_csv('data/alameda.csv')

@app.route("/bar")
def data_bar():
    chart = Chart(data=alameda, height=HEIGHT, width=WIDTH).mark_bar(color='lightgreen').encode(
        X('year:O', axis=Axis(title='Year')),
        Y('total_prison_pop', axis=Axis(title='Total Prison Population'))
    )
    return chart.to_json()

if __name__ == '__main__':
    app.run(port=5000, debug=True)