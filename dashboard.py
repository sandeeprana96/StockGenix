import dash
import dash_table
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import tweepy
import pandas as pd
import requests as req
import numpy as np


consumer_key = "djpjn7IJehQHgq8UQlJYO9sl0"
consumer_secret = "P7kPhCXpmRKenXhNccs1NwiVWjqIojPuQVrTk58vfI2E9hnNVh"
access_token = "1405894071327985664-9xYjhQhBYbG5M0xvstpExQ4Tmb0HQy"
access_token_secret = "QCPouVU2f3Ywmcw2oKYV6wBOQCw00eoRSRWA0Nibv8NDf"

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

number_of_tweets = 200
tweets = []
likes = []
time = []

for i in tweepy.Cursor(api.user_timeline, id="elonmusk", tweet_mode="extended").items(number_of_tweets):
    tweets.append(i.full_text)
    likes.append(i.favorite_count)
    time.append(i.created_at)

df = pd.DataFrame({'tweets': tweets, 'likes': likes, 'time': time})
# df = df[~df.tweets.str.contains("RT")]
# df = df.reset_index(drop=True)
df.to_csv("tweetdata.csv", mode='a', index=False, header=False)

# GitHub repos URLs
url_confirmed = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv"

url_deaths = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv"

url_recovered = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv"

# Get the data into the app
confirmed = pd.read_csv(url_confirmed)
deaths = pd.read_csv(url_deaths)
recovered = pd.read_csv(url_recovered)
stock_data = pd.read_csv("StockData.csv")
top4stockdata = stock_data.nlargest(4, columns="Debt to Equity")
tweet_data = pd.read_csv("TweetsWithSentimentFlag.csv")
tweet_data.style.apply(
    lambda x: ['background:green' if x == 1 else 'background:yellow' if x == 0 else 'background:red' for x in
               tweet_data.Sentiment], axis=0)
titles = list(tweet_data.columns)
titles[0], titles[1] = titles[1], titles[0]
tweet_data = tweet_data[titles]

# Unpivot the data frames
total_confirmed = confirmed.melt(
    id_vars=["Province/State", "Country/Region", "Lat", "Long"],
    value_vars=confirmed.columns[4:],
    var_name="date",
    value_name="confirmed"
)

total_deaths = deaths.melt(
    id_vars=["Province/State", "Country/Region", "Lat", "Long"],
    value_vars=deaths.columns[4:],
    var_name="date",
    value_name="deaths"
)

total_recovered = recovered.melt(
    id_vars=["Province/State", "Country/Region", "Lat", "Long"],
    value_vars=recovered.columns[4:],
    var_name="date",
    value_name="recovered"
)

# Merge data frames
covid_data = total_confirmed.merge(
    right=total_deaths,
    how="left",
    on=["Province/State", "Country/Region", "date", "Lat", "Long"]
).merge(
    right=total_recovered,
    how="left",
    on=["Province/State", "Country/Region", "date", "Lat", "Long"]
)

# Wrangle data
covid_data["recovered"] = covid_data["recovered"].fillna(0)
covid_data["active"] = covid_data["confirmed"] - covid_data["deaths"] - covid_data["recovered"]
covid_data["date"] = pd.to_datetime(covid_data["date"])

# Daily totals
covid_data_1 = covid_data.groupby(["date"])[["confirmed", "deaths", "recovered", "active"]].sum().reset_index()

# Create dict of list
covid_data_list = covid_data[["Country/Region", "Lat", "Long"]]
dict_of_locations = covid_data_list.set_index("Country/Region")[["Lat", "Long"]].T.to_dict("dict")

# Instanciate the app
app = dash.Dash(__name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}])


def generate_list(dataframe, max_rows=10):
    return html.Div([
        dataframe.to_html()]

    )


# Build the layout
app.layout = html.Div(
    children=[
        # (First row) Header: Logo - Title - Last updated
        html.Div(
            children=[
                # Logo
                html.Div(
                    children=[
                        html.Img(
                            src=app.get_asset_url("stockgenix-logo.jpg"),
                            id="corona-image",
                            style={
                                "height": "60px",
                                "width": "auto",
                                "margin-bottom": "25px"
                            }
                        )
                    ],
                    className="one-third column"
                ),
                html.Div(
                    children=[
                        # Title and subtitle
                        html.Div(
                            children=[
                                html.H3(
                                    children="Twitter",
                                    style={
                                        "margin-bottom": "0",
                                        "color": "white"
                                    }
                                ),
                                html.H5(
                                    children="Sentiment Analysis",
                                    style={
                                        "margin-bottom": "0",
                                        "color": "white"
                                    }
                                )
                            ]
                        )
                    ],
                    className="one-half column",
                    id='title'
                ),
                # Last updated
                html.Div(
                    children=[
                        html.H6(
                            children="Last Updated " + str(covid_data["date"].iloc[-1].strftime("%B %d, %Y")),
                            style={
                                "color": "orange"
                            }
                        )
                    ],
                    className="one-thid column",
                    id="title1"
                )
            ],
            id="header",
            className="row flex-display",
            style={
                "margin-bottom": "25px"
            }
        ),
        # (Second row) Cards: Global cases - Global deaths - Global recovered - Global active
        html.Div(
            children=[
                # (Column 1): Global cases
                html.Div(
                    children=[
                        # Title
                        html.H6(
                            children=top4stockdata.iloc[0]["Company Name"],
                            style={
                                "textAlign": "center",
                                "color": "white"
                            }
                        ),
                        # Total v
                        html.P(
                            children="Sales Growth: " + top4stockdata.iloc[0]["Sales Growth"],
                            style={
                                "textAlign": "center",
                                "color": "orange",
                                "fontSize": 20
                            }
                        ),
                        # New active
                        html.P(
                            children="5yr Profit Growth: " + top4stockdata.iloc[0]["5yr Profit Growth"],
                            style={
                                "textAlign": "center",
                                "color": "orange",
                                "fontSize": 15,
                                "margin-top": "-10px"
                            }
                        ),
                        # New active
                        html.P(
                            children="Debt to Equity: " + str(top4stockdata.iloc[0]["Debt to Equity"]),
                            style={
                                "textAlign": "center",
                                "color": "orange",
                                "fontSize": 15,
                                "margin-top": "-10px"
                            }
                        ),
                        # New active
                        html.P(
                            children="ROE: " + top4stockdata.iloc[0]["ROE"],
                            style={
                                "textAlign": "center",
                                "color": "orange",
                                "fontSize": 15,
                                "margin-top": "-10px"
                            }
                        )
                    ],
                    className="card_container three columns"
                ),
                # (Column 2): Global deaths
                html.Div(
                    children=[
                        # Title
                        html.H6(
                            children=top4stockdata.iloc[1]["Company Name"],
                            style={
                                "textAlign": "center",
                                "color": "white"
                            }
                        ),
                        # Total v
                        html.P(
                            children="Sales Growth: " + top4stockdata.iloc[1]["Sales Growth"],
                            style={
                                "textAlign": "center",
                                "color": "#dd1e35",
                                "fontSize": 20
                            }
                        ),
                        # New active
                        html.P(
                            children="5yr Profit Growth: " + top4stockdata.iloc[1]["5yr Profit Growth"],
                            style={
                                "textAlign": "center",
                                "color": "#dd1e35",
                                "fontSize": 15,
                                "margin-top": "-10px"
                            }
                        ),
                        # New active
                        html.P(
                            children="Debt to Equity: " + str(top4stockdata.iloc[1]["Debt to Equity"]),
                            style={
                                "textAlign": "center",
                                "color": "#dd1e35",
                                "fontSize": 15,
                                "margin-top": "-10px"
                            }
                        ),
                        # New active
                        html.P(
                            children="ROE: " + top4stockdata.iloc[1]["ROE"],
                            style={
                                "textAlign": "center",
                                "color": "#dd1e35",
                                "fontSize": 15,
                                "margin-top": "-10px"
                            }
                        )
                    ],
                    className="card_container three columns"
                ),
                # (Column 3): Global recovered
                html.Div(
                    children=[
                        # Title
                        html.H6(
                            children=top4stockdata.iloc[2]["Company Name"],
                            style={
                                "textAlign": "center",
                                "color": "white"
                            }
                        ),
                        # Total v
                        html.P(
                            children="Sales Growth: " + top4stockdata.iloc[2]["Sales Growth"],
                            style={
                                "textAlign": "center",
                                "color": "green",
                                "fontSize": 20
                            }
                        ),
                        # New active
                        html.P(
                            children="5yr Profit Growth: " + top4stockdata.iloc[2]["5yr Profit Growth"],
                            style={
                                "textAlign": "center",
                                "color": "green",
                                "fontSize": 15,
                                "margin-top": "-10px"
                            }
                        ),
                        # New active
                        html.P(
                            children="Debt to Equity: " + str(top4stockdata.iloc[2]["Debt to Equity"]),
                            style={
                                "textAlign": "center",
                                "color": "green",
                                "fontSize": 15,
                                "margin-top": "-10px"
                            }
                        ),
                        # New active
                        html.P(
                            children="ROE: " + top4stockdata.iloc[2]["ROE"],
                            style={
                                "textAlign": "center",
                                "color": "green",
                                "fontSize": 15,
                                "margin-top": "-10px"
                            }
                        )
                    ],
                    className="card_container three columns"
                ),
                # (Column 4): Global active
                html.Div(
                    children=[
                        # Title
                        html.H6(
                            children=top4stockdata.iloc[3]["Company Name"],
                            style={
                                "textAlign": "center",
                                "color": "white"
                            }
                        ),
                        # Total v
                        html.P(
                            children="Sales Growth: " + top4stockdata.iloc[3]["Sales Growth"],
                            style={
                                "textAlign": "center",
                                "color": "#e55467",
                                "fontSize": 20
                            }
                        ),
                        # New active
                        html.P(
                            children="5yr Profit Growth: " + top4stockdata.iloc[3]["5yr Profit Growth"],
                            style={
                                "textAlign": "center",
                                "color": "#e55467",
                                "fontSize": 15,
                                "margin-top": "-10px"
                            }
                        ),
                        # New active
                        html.P(
                            children="Debt to Equity: " + str(top4stockdata.iloc[3]["Debt to Equity"]),
                            style={
                                "textAlign": "center",
                                "color": "#e55467",
                                "fontSize": 15,
                                "margin-top": "-10px"
                            }
                        ),
                        # New active
                        html.P(
                            children="ROE: " + top4stockdata.iloc[3]["ROE"],
                            style={
                                "textAlign": "center",
                                "color": "#e55467",
                                "fontSize": 15,
                                "margin-top": "-10px"
                            }
                        )
                    ],
                    className="card_container three columns"
                )
            ],
            className="row flex-display"
        ),
        # (Third row): Value boxes - Donut chart - Line & Bars
        html.Div(
            children=[
                # (Column 1) Value boxes
                html.Div(
                    children=[
                        # (Row 1) Country selector
                        html.P(
                            children="Select Company: ",
                            className="fix_label",
                            style={
                                "color": "white"
                            }
                        ),
                        dcc.Dropdown(
                            id="w_countries",
                            multi=False,
                            searchable=True,
                            value="Uruguay",
                            placeholder="Select Company",
                            options=[{"label": c, "value": c} for c in (stock_data["Company Name"].unique())],
                            className="dcc_compon"
                        ),
                        # (Row 2) New cases title
                        html.P(
                            children="New cases: " + " " + str(covid_data["date"].iloc[-1].strftime("%B %d, %Y")),
                            className="fix_label",
                            style={
                                "textAlign": "center",
                                "color": "white"
                            }
                        ),
                        # (Row 3) New confirmed
                        dcc.Graph(
                            id="confirmed",
                            config={
                                "displayModeBar": False
                            },
                            className="dcc_compo",
                            style={
                                "margin-top": "20px"
                            }
                        ),
                        # (Row 4) New deaths
                        dcc.Graph(
                            id="deaths",
                            config={
                                "displayModeBar": False
                            },
                            className="dcc_compo",
                            style={
                                "margin-top": "20px"
                            }
                        ),
                        # (Row 5) New recovered
                        dcc.Graph(
                            id="recovered",
                            config={
                                "displayModeBar": False
                            },
                            className="dcc_compo",
                            style={
                                "margin-top": "20px"
                            }
                        ),
                        # (Row 6) New active
                        dcc.Graph(
                            id="active",
                            config={
                                "displayModeBar": False
                            },
                            className="dcc_compo",
                            style={
                                "margin-top": "20px"
                            }
                        )
                    ],
                    className="create_container three columns"
                ),
                # (Column 2) Donut chart
                html.Div(
                    children=[
                        # Donut chart
                        dcc.Graph(
                            id="pie_chart",
                            config={
                                "displayModeBar": "hover"
                            }
                        )
                    ],
                    className="create_container four columns",
                    style={
                        "maxWidth": "400px"
                    }
                ),
                # (Columns 3 & 4) Line and bars plot
                html.Div(
                    children=[
                        dcc.Graph(
                            id="line_chart",
                            config={
                                "displayModeBar": "hover"
                            }
                        )
                    ],
                    className="create_container five columns"
                )
            ],
            className="row flex-display"
        ),
        html.Div(
            children=[
                html.Div(
                    children=["Test"]
                )
            ],
            className="row flex-display"
        ),
        # (Fourth Row) Tweets
        html.Div(
            children=[
                html.Div(
                    children=[
                        dash_table.DataTable(
                            id='table',
                            columns=[{"name": i, "id": i} for i in tweet_data.columns],
                            tooltip_data=[
                                {
                                    column: {'value': str(value),
                                             'type': 'markdown'}
                                    for column, value in row.items()
                                } for row in tweet_data.to_dict('records')
                            ],
                            tooltip_delay=0,
                            tooltip_duration=None,
                            style_cell={
                                'overflow': 'hidden',
                                'textOverflow': 'ellipsis',
                                'maxWidth': 0,
                                'textAlign': 'left',
                                'background': '#1f2c56',
                                'color': 'white',
                                'border': 'none',
                                'font-size': '1em',
                                'font-weight': '400',
                                'font-family': 'Open Sans, HelveticaNeue, Helvetica Neue, Helvetica, Arial, sans-serif'
                            },
                            style_header={
                                'fontWeight': 'bold',
                                'font-size': '1.5em',
                            },
                            style_cell_conditional=[
                                {'if': {'column_id': 'ID'},
                                 'width': '20%'},
                                {'if': {'column_id': 'Tweets'},
                                 'width': '60%'}
                            ],
                            style_data_conditional=[
                                {
                                    'if': {
                                        'filter_query': '{Sentiment} = 1',
                                        'column_id': 'Tweets'
                                    },
                                    'color': 'green'
                                },
                                {
                                    'if': {
                                        'filter_query': '{Sentiment} = 0',
                                        'column_id': 'Tweets'
                                    },
                                    'color': 'yellow'
                                },
                                {
                                    'if': {
                                        'filter_query': '{Sentiment} = -1',
                                        'column_id': 'Tweets'
                                    },
                                    'color': 'red'
                                }
                            ],
                            style_as_list_view=True,
                            data=tweet_data.to_dict('records'),
                        )
                    ],
                    className="create_container1 twelve columns",
                )
            ],
            className="row flex-display"
        )
    ],
    id="mainContainer",
    style={
        "display": "flex",
        "flex-direction": "column"
    }
)


# Build the callbacks

# New confirmed cases value box
@app.callback(
    Output(
        component_id="confirmed",
        component_property="figure"
    ),
    Input(
        component_id="w_countries",
        component_property="value"
    )
)
def update_confirmed(w_countries):
    # Filter the data
    covid_data_2 = covid_data.groupby(["date", "Country/Region"])[
        ["confirmed", "deaths", "recovered", "active"]].sum().reset_index()
    # Calculate values
    value_confirmed = covid_data_2[covid_data_2["Country/Region"] == w_countries]["confirmed"].iloc[-1] - \
                      covid_data_2[covid_data_2["Country/Region"] == w_countries]["confirmed"].iloc[-2]
    delta_confirmed = covid_data_2[covid_data_2["Country/Region"] == w_countries]["confirmed"].iloc[-1] - \
                      covid_data_2[covid_data_2["Country/Region"] == w_countries]["confirmed"].iloc[-3]
    # Build the figure
    fig = {
        "data": [
            go.Indicator(
                mode="number+delta",
                value=value_confirmed,
                delta={
                    "reference": delta_confirmed,
                    "position": "right",
                    "valueformat": ",g",
                    "relative": False,
                    "font": {
                        "size": 15
                    }
                },
                number={
                    "valueformat": ",",
                    "font": {
                        "size": 20
                    }
                },
                domain={
                    "y": [0, 1],
                    "x": [0, 1]
                }
            )
        ],
        "layout": go.Layout(
            title={
                "text": "New confirmed",
                "y": 1,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top"
            },
            font={
                "color": "orange"
            },
            paper_bgcolor="#1f2c56",
            plot_bgcolor="#1f2c56",
            height=50
        )
    }
    # Return the figure
    return fig


# Deaths value box
@app.callback(
    Output(
        component_id="deaths",
        component_property="figure"
    ),
    Input(
        component_id="w_countries",
        component_property="value"
    )
)
def update_deaths(w_countries):
    # Filter the data
    covid_data_2 = covid_data.groupby(["date", "Country/Region"])[
        ["confirmed", "deaths", "recovered", "active"]].sum().reset_index()
    # Calculate values
    value_deaths = covid_data_2[covid_data_2["Country/Region"] == w_countries]["deaths"].iloc[-1] - \
                   covid_data_2[covid_data_2["Country/Region"] == w_countries]["deaths"].iloc[-2]
    delta_deaths = covid_data_2[covid_data_2["Country/Region"] == w_countries]["deaths"].iloc[-1] - \
                   covid_data_2[covid_data_2["Country/Region"] == w_countries]["deaths"].iloc[-3]
    # Build the figure
    fig = {
        "data": [
            go.Indicator(
                mode="number+delta",
                value=value_deaths,
                delta={
                    "reference": delta_deaths,
                    "position": "right",
                    "valueformat": ",g",
                    "relative": False,
                    "font": {
                        "size": 15
                    }
                },
                number={
                    "valueformat": ",",
                    "font": {
                        "size": 20
                    }
                },
                domain={
                    "y": [0, 1],
                    "x": [0, 1]
                }
            )
        ],
        "layout": go.Layout(
            title={
                "text": "New deaths",
                "y": 1,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top"
            },
            font={
                "color": "#dd1e35"
            },
            paper_bgcolor="#1f2c56",
            plot_bgcolor="#1f2c56",
            height=50
        )
    }
    # Return the figure
    return fig


# Recovered value box
@app.callback(
    Output(
        component_id="recovered",
        component_property="figure"
    ),
    Input(
        component_id="w_countries",
        component_property="value"
    )
)
def update_recovered(w_countries):
    # Filter the data
    covid_data_2 = covid_data.groupby(["date", "Country/Region"])[
        ["confirmed", "deaths", "recovered", "active"]].sum().reset_index()
    # Calculate values
    value_recovered = covid_data_2[covid_data_2["Country/Region"] == w_countries]["recovered"].iloc[-1] - \
                      covid_data_2[covid_data_2["Country/Region"] == w_countries]["recovered"].iloc[-2]
    delta_recovered = covid_data_2[covid_data_2["Country/Region"] == w_countries]["recovered"].iloc[-1] - \
                      covid_data_2[covid_data_2["Country/Region"] == w_countries]["recovered"].iloc[-3]
    # Build the figure
    fig = {
        "data": [
            go.Indicator(
                mode="number+delta",
                value=value_recovered,
                delta={
                    "reference": delta_recovered,
                    "position": "right",
                    "valueformat": ",g",
                    "relative": False,
                    "font": {
                        "size": 15
                    }
                },
                number={
                    "valueformat": ",",
                    "font": {
                        "size": 20
                    }
                },
                domain={
                    "y": [0, 1],
                    "x": [0, 1]
                }
            )
        ],
        "layout": go.Layout(
            title={
                "text": "New recovered",
                "y": 1,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top"
            },
            font={
                "color": "green"
            },
            paper_bgcolor="#1f2c56",
            plot_bgcolor="#1f2c56",
            height=50
        )
    }
    # Return the figure
    return fig


# Recovered value box
@app.callback(
    Output(
        component_id="active",
        component_property="figure"
    ),
    Input(
        component_id="w_countries",
        component_property="value"
    )
)
def update_active(w_countries):
    # Filter the data
    covid_data_2 = covid_data.groupby(["date", "Country/Region"])[
        ["confirmed", "deaths", "recovered", "active"]].sum().reset_index()
    # Calculate values
    value_active = covid_data_2[covid_data_2["Country/Region"] == w_countries]["active"].iloc[-1] - \
                   covid_data_2[covid_data_2["Country/Region"] == w_countries]["active"].iloc[-2]
    delta_active = covid_data_2[covid_data_2["Country/Region"] == w_countries]["active"].iloc[-1] - \
                   covid_data_2[covid_data_2["Country/Region"] == w_countries]["active"].iloc[-3]
    # Build the figure
    fig = {
        "data": [
            go.Indicator(
                mode="number+delta",
                value=value_active,
                delta={
                    "reference": delta_active,
                    "position": "right",
                    "valueformat": ",g",
                    "relative": False,
                    "font": {
                        "size": 15
                    }
                },
                number={
                    "valueformat": ",",
                    "font": {
                        "size": 20
                    }
                },
                domain={
                    "y": [0, 1],
                    "x": [0, 1]
                }
            )
        ],
        "layout": go.Layout(
            title={
                "text": "New active",
                "y": 1,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top"
            },
            font={
                "color": "#e55467"
            },
            paper_bgcolor="#1f2c56",
            plot_bgcolor="#1f2c56",
            height=50
        )
    }
    # Return the figure
    return fig


# Donut chart
@app.callback(
    Output(
        component_id="pie_chart",
        component_property="figure"
    ),
    Input(
        component_id="w_countries",
        component_property="value"
    )
)
def update_pie_chart(w_countries):
    # Filter the data
    covid_data_2 = covid_data.groupby(["date", "Country/Region"])[
        ["confirmed", "deaths", "recovered", "active"]].sum().reset_index()
    # Calculate values
    confirmed_value = covid_data_2[covid_data_2["Country/Region"] == w_countries]["confirmed"].iloc[-1]
    deaths_value = covid_data_2[covid_data_2["Country/Region"] == w_countries]["deaths"].iloc[-1]
    recovered_value = covid_data_2[covid_data_2["Country/Region"] == w_countries]["recovered"].iloc[-1]
    active_value = covid_data_2[covid_data_2["Country/Region"] == w_countries]["active"].iloc[-1]
    # List of colors
    colors = ["orange", "#dd1e35", "green", "#e55467"]
    # Build the figure
    fig = {
        "data": [
            go.Pie(
                labels=["Confirmed", "Deaths", "Recovered", "Active"],
                values=[confirmed_value, deaths_value, recovered_value, active_value],
                marker={
                    "colors": colors
                },
                hoverinfo="label+value+percent",
                textinfo="label+value",
                hole=0.7,
                rotation=45,
                insidetextorientation="radial"
            )
        ],
        "layout": go.Layout(
            title={
                "text": f"Total cases {w_countries}",
                "y": 0.93,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top"
            },
            titlefont={
                "color": "white",
                "size": 20
            },
            font={
                "family": "sans-serif",
                "color": "white",
                "size": 12
            },
            hovermode="closest",
            paper_bgcolor="#1f2c56",
            plot_bgcolor="#1f2c56",
            legend={
                "orientation": "h",
                "bgcolor": "#1f2c56",
                "xanchor": "center",
                "x": 0.5,
                "y": -0.7
            }
        )
    }
    # Return the figure
    return fig


# Line and bars chart
@app.callback(
    Output(
        component_id="line_chart",
        component_property="figure"
    ),
    Input(
        component_id="w_countries",
        component_property="value"
    )
)
def update_line_chart(w_countries):
    # Filter the data
    covid_data_2 = covid_data.groupby(["date", "Country/Region"])[
        ["confirmed", "deaths", "recovered", "active"]].sum().reset_index()
    covid_data_3 = covid_data_2[covid_data_2["Country/Region"] == w_countries][
        ["Country/Region", "date", "confirmed"]].reset_index()
    covid_data_3["daily_confirmed"] = covid_data_3["confirmed"] - covid_data_3["confirmed"].shift(1)
    covid_data_3["rolling_avg"] = covid_data_3["daily_confirmed"].rolling(window=7).mean()
    # Build the figure
    fig = {
        "data": [
            go.Bar(
                x=covid_data_3["date"].tail(30),
                y=covid_data_3["daily_confirmed"].tail(30),
                name="Daily confirmed cases",
                marker={
                    "color": "orange"
                },
                hoverinfo="text",
                hovertemplate="<b>Date</b>: %{x} <br><b>Daily confirmed</b>: %{y:,.0f}<extra></extra>"
            ),
            go.Scatter(
                x=covid_data_3["date"].tail(30),
                y=covid_data_3["rolling_avg"].tail(30),
                name="Rolling avg. of the last 7 days - daily confirmed cases",
                mode="lines",
                line={
                    "width": 3,
                    "color": "#ff00ff"
                },
                hoverinfo="text",
                hovertemplate="<b>Date</b>: %{x} <br><b>Rolling Avg.</b>: %{y:,.0f}<extra></extra>"
            )
        ],
        "layout": go.Layout(
            title={
                "text": f"Last 30 days daily confirmed cases: {w_countries}",
                "y": 0.93,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top"
            },
            titlefont={
                "color": "white",
                "size": 20
            },
            xaxis={
                "title": "<b>Date</b>",
                "color": "white",
                "showline": True,
                "showgrid": True,
                "showticklabels": True,
                "linecolor": "white",
                "linewidth": 1,
                "ticks": "outside",
                "tickfont": {
                    "family": "Aerial",
                    "color": "white",
                    "size": 12
                }
            },
            yaxis={
                "title": "<b>Confirmed cases</b>",
                "color": "white",
                "showline": True,
                "showgrid": True,
                "showticklabels": True,
                "linecolor": "white",
                "linewidth": 1,
                "ticks": "outside",
                "tickfont": {
                    "family": "Aerial",
                    "color": "white",
                    "size": 12
                }
            },
            font={
                "family": "sans-serif",
                "color": "white",
                "size": 12
            },
            hovermode="closest",
            paper_bgcolor="#1f2c56",
            plot_bgcolor="#1f2c56",
            legend={
                "orientation": "h",
                "bgcolor": "#1f2c56",
                "xanchor": "center",
                "x": 0.5,
                "y": -0.7
            }
        )
    }
    # Return the figure
    return fig


# Map
@app.callback(
    Output(
        component_id="map_chart",
        component_property="figure"
    ),
    Input(
        component_id="w_countries",
        component_property="value"
    )
)
def update_map(w_countries):
    # Filter the data
    covid_data_4 = covid_data.groupby(["Lat", "Long", "Country/Region"])[
        ["confirmed", "deaths", "recovered", "active"]].max().reset_index()
    covid_data_5 = covid_data_4[covid_data_4["Country/Region"] == w_countries]
    # Get zoom
    if w_countries:
        zoom = 2
        zoom_lat = dict_of_locations[w_countries]["Lat"]
        zoom_long = dict_of_locations[w_countries]["Long"]
    # Build the figure
    fig = {
        "data": [
            go.Scattermapbox(
                lon=covid_data_5["Long"],
                lat=covid_data_5["Lat"],
                mode="markers",
                marker=go.scattermapbox.Marker(
                    size=covid_data_5["confirmed"] / 1500,
                    color=covid_data_5["confirmed"],
                    colorscale="HSV",
                    showscale=False,
                    sizemode="area",
                    opacity=0.3
                ),
                hoverinfo="text",
                hovertemplate="<b>Country:</b> " + covid_data_5["Country/Region"].astype(str) + "<br>" +
                              "<b>Confirmed cases:</b> " + [f'{x:,.0f}' for x in covid_data_5["confirmed"]] + "<br>" +
                              "<b>Deaths:</b> " + [f'{x:,.0f}' for x in covid_data_5["confirmed"]] + "<br>" +
                              "<b>Recovered:</b> " + [f'{x:,.0f}' for x in covid_data_5["recovered"]] + "<br>" +
                              "<b>Active:</b> " + [f'{x:,.0f}' for x in covid_data_5["active"]] + "<extra></extra>"
            )
        ],
        "layout": go.Layout(
            hovermode="x",
            paper_bgcolor="#1f2c56",
            plot_bgcolor="#1f2c56",
            margin={
                "r": 0,
                "l": 0,
                "t": 0,
                "b": 0
            },
            mapbox=dict(
                accesstoken="pk.eyJ1IjoicXM2MjcyNTI3IiwiYSI6ImNraGRuYTF1azAxZmIycWs0cDB1NmY1ZjYifQ.I1VJ3KjeM-S613FLv3mtkw",
                center=go.layout.mapbox.Center(
                    lat=zoom_lat,
                    lon=zoom_long
                ),
                style="dark",
                zoom=zoom
            ),
            autosize=True
        )
    }
    # Return the figure
    return fig


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
