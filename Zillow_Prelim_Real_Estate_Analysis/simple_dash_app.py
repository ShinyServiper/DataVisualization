
# All Necessary Packages
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import pandas as pd                # for working with DataFrames
import plotly.express as px        # for plotting; alias created                        
import os                          # imported for interacting with the operating system
from datetime import datetime      # imported to work with date strings
import geopandas

# Changes directory to the current working directory
os.chdir(os.getcwd())            

# This dictionary is for Title Mappings
title_mappings={"Estimated Price to Rent Ratio":"PTR","Median Percent of Price Cuts":"PercentPriceCut",
"Zillow Observed Rent Index":"RentPrice","Zillow Home Value Index":"HomePrice"}

# This dictionary is for color Mappings
color_mappings={"Estimated Price to Rent Ratio":"tealrose","Median Percent of Price Cuts":"sunset",
"Zillow Observed Rent Index":"darkmint","Zillow Home Value Index":"haline"}


#Function for getting all dates in the same format, provided they are different among multiple files
def dateNormalize(listOfDates):
    listOfDates=[datetime.strptime(datetime.strptime(this_date,"%Y-%m-%d").strftime("%Y-%m"),"%Y-%m") if (len(this_date.split("-")) ==3 ) else datetime.strptime(this_date,
    "%Y-%m") for this_date in listOfDates]
    return listOfDates


# Load state shape files
states=geopandas.read_file("cb_2018_us_state_500k.zip")

# Reading in the data from the folder
rent_prices=pd.read_csv("./RealEstate_Data/Zillow_ZORI_Index.csv",parse_dates=True)
home_prices=pd.read_csv("./RealEstate_Data/Zillow_ZHVI_Index.csv",parse_dates=True)
median_price_cut_perc=pd.read_csv("./RealEstate_Data/Zillow_Mean_Percent_Cut.csv",parse_dates=True)


# Removing unecessary columns
rent_prices.drop(columns=["RegionID","SizeRank"],inplace=True)
home_prices.drop(columns=["RegionID","SizeRank","RegionType"],inplace=True)
median_price_cut_perc.drop(columns=["RegionID","SizeRank","RegionType"],inplace=True)


# Dropping the National Average Column
rent_prices=rent_prices.iloc[1:,:]
home_prices=home_prices.iloc[1:,:]
median_price_cut_perc=median_price_cut_perc.iloc[1:,:]


# Adding a StateName column to rent_prices DataFrame (when necessary)
rent_prices["StateName"]=[location[-2:] for location in list(rent_prices["RegionName"])]


# Reorder columns (when necessary)
rent_prices=rent_prices[["RegionName","StateName"]+list(rent_prices.columns[[not (item.isalpha()) for item in list(rent_prices.columns)]])]

#Extract most recent data
rent_recent_values=rent_prices.iloc[:,[1,-1]]
home_recent_values=home_prices.iloc[:,[1,-1]]
median_price_cut_perc_recent_values=median_price_cut_perc.iloc[:,[1,-1]]


#Compute Median Values by States
rent_recent_values=rent_recent_values.groupby("StateName").median()
home_recent_values=home_recent_values.groupby("StateName").median()
median_price_cut_perc_recent_values=median_price_cut_perc_recent_values.groupby("StateName").median()


#Reshaping the Vectors using the "melt" method
home_prices=home_prices.melt(id_vars=('RegionName','StateName'),value_vars=list(home_prices.columns)[2:],
var_name="Date", value_name="HomePrice")

rent_prices=rent_prices.melt(id_vars=('RegionName','StateName'),value_vars=list(rent_prices.columns)[2:],
var_name="Date", value_name="RentPrice")

median_price_cut_perc=median_price_cut_perc.melt(id_vars=('RegionName','StateName'),value_vars=list(median_price_cut_perc.columns)[2:],
var_name="Date", value_name="PercentPriceCut")


#Normalizing the Dates (Making dates the same format)
median_price_cut_perc["Date"]=dateNormalize(list(median_price_cut_perc["Date"]))
home_prices["Date"]=dateNormalize(list(home_prices["Date"]))
rent_prices["Date"]=dateNormalize(list(rent_prices["Date"]))


#Prepping Index to Join DataFrames
rent_recent_values.index.name="STUSPS"
rent_recent_values.columns=["RentPrice"]

home_recent_values.index.name="STUSPS"
home_recent_values.columns=["HomePrice"]

median_price_cut_perc_recent_values.index.name="STUSPS"
median_price_cut_perc_recent_values.columns=["PercentPriceCut"]


# Set the index for "states" DataFrame containing shape
states=states.set_index("STUSPS")

#Making one big "states" GeoFrame
states=pd.merge(pd.merge(states,rent_recent_values,on="STUSPS",how="inner"),home_recent_values,on="STUSPS",how="inner")
states=pd.merge(states,median_price_cut_perc_recent_values,on="STUSPS",how="inner")

# Creating Price to Rent Ratio measure and conversion to percents in GeoFrame
states["PTR"]=states["HomePrice"]/(12*states["RentPrice"])
states["PercentPriceCut"]=100*states["PercentPriceCut"]

# Resetting Index to prepare for plotting
states.reset_index(inplace=True)
states.dropna(inplace=True)

# creating the real estate DataFrame
real_estate_df=pd.merge(pd.merge(home_prices.set_index(["RegionName","StateName","Date"]),rent_prices.set_index(["RegionName","StateName","Date"]),
left_index=True,right_index=True),median_price_cut_perc.set_index(["RegionName","StateName","Date"]),left_index=True, right_index=True)


#Computing Price to Rent Ratio and Converting to Percent Values
real_estate_df["PTR"]=real_estate_df["HomePrice"]/(12*real_estate_df["RentPrice"])
real_estate_df["PercentPriceCut"]=100*real_estate_df["PercentPriceCut"]

# Resetting Index to prepare for plotting
real_estate_df.reset_index(inplace=True)
real_estate_df.dropna(inplace=True)


# Collecting Metric Display Options
MetricOptions=list(color_mappings.keys())

# Get unique states and order them alphabetically
StateNames=list(real_estate_df["StateName"].unique()) # get unique states
StateNames.sort(reverse=False)

# Creating the Labels for Dropdown menus in application
labels=[{'label':i,"value":i} for i in StateNames]
labels2=[{'label':i, "value":i} for i in MetricOptions]

#list_prices["Date"]=datetime.strptime(list(list_prices["Date"]),"%Y-%m-%d")
fig=px.line(real_estate_df[real_estate_df["StateName"] == "NC"],x="Date",y="RentPrice",line_group="RegionName",
color="RegionName",template="plotly_dark",  #width=800, height=600,
hover_name="RegionName",hover_data={"RegionName":False},title="Analysis By City",markers="-o")
fig.update_traces(hovertemplate='Date: %{x} <br>RentPrice: %{y}')
fig.update_layout(title={"x":.5,"xanchor":"center"},font={"size":16,"color":"#7FDBFF"})


#states=states.set_index("STUSPS")
#states=pd.merge(states,recent_value,on="STUSPS",how="inner")
#states.reset_index(inplace=True)

color_max=1.2*states["RentPrice"].max() # finding max value for the color map
fig2=px.choropleth(states,geojson=states.geometry,locations=states.STUSPS,locationmode="USA-states",
scope="usa",hover_name=states.STUSPS,template="plotly_dark",color="RentPrice",color_continuous_scale="darkmint",
title="National View: Zillow Observed Rent Index",range_color=[0,color_max])
fig2.update_layout(title={"x":.5,"xanchor":"center"},font={"size":16,"color":"#7FDBFF"})


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
#external_stylesheets=external_stylesheets
####################        STRUCTURE OF APPLICATION         #####################
app=dash.Dash(__name__,external_stylesheets=external_stylesheets)

# Defining Colors to Use
colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}



app.layout = html.Div(style={'backgroundColor': colors['background'],"width":"100%"},children=[
    html.H1(
        children='Preliminary Real Estate Analysis',
        style={
            'textAlign': 'center',
            'color': colors['text'],
        }
    ),
    html.Div(children=
    """Application using available research data from Zillow. Choose a state and and metric to begin 
    your analysis.""", style={
        'textAlign': 'center',
        'color': colors['text'],
        "height":"30px"
    },
    
    
    ),

######   MAKING THE DROPDOWN MENUS AND THE FIGURES    #########
    html.Div(style={'backgroundColor': "colors['background']","color":"black","height":"600px"},
        children=[html.Div(dcc.Dropdown(className="select",style={"backgroundColor":"transparent","color":"black","postion":"absolute","max-width":"500px"},id="dropdown",
    placeholder="Select a state",options=labels,value="NC")),html.Div(dcc.Dropdown(style={"color":"black","backgroundColor":"transparent","postion":"right","max-width":"500px","height":"55 px"},id="dropdown2",
    placeholder="Select a metric",options=labels2,value="Zillow Observed Rent Index")),
            html.Div(
                dcc.Graph(
                    style={"float":"left","width":"55%","height":"500px"
                    },id="fig1",figure=fig
                )
            ),
            html.Div(
                dcc.Graph(
                    style={"float":"right","width":"45%","height":"500px"
                    },id="fig2",figure=fig2
                )
            )
        ],
    ),
    
        ] #dcc.Graph(id="fig1",figure=fig)
)

#############     TO UPDATE THE TIME SERIES BY STATE      ################

###### Defining Our Callback Function
#@app.callback(Output("fig","figure"),
#    Input("dropdown","value"))

###### Defining the Action Function
#def update_graph(state):

#    fig=px.line(real_estate_df[real_estate_df["StateName"] == state],x="Date",y="RentPrice",line_group="RegionName",
#    color="RegionName",template="plotly_dark",  #width=800, height=600,
#    hover_name="RegionName",hover_data={"RegionName":False},title="Recorded Cities in "+state,markers="-o")
#    fig.update_traces(hovertemplate='Date: %{x} <br>RentPrice: %{y}')
#    fig.update_layout(title={"x":.5,"xanchor":"center"},font={"size":16,"color":"#7FDBFF"})
#    return fig
@app.callback(
    Output("fig1","figure"),
    Input("dropdown","value"),
    Input("dropdown2","value"))

def update_graph(state,metric):
    metric_string='%s' %title_mappings[metric]
    metric_string2="Date: %{x} <br>"+metric_string+": %{y}"
    fig=px.line(real_estate_df[real_estate_df["StateName"] == state],x="Date",y=title_mappings[metric],line_group="RegionName",
    color="RegionName",template="plotly_dark",  #width=800, height=600,
    hover_name="RegionName",hover_data={"RegionName":False},title="Recorded Cities in "+state,markers="-o")
    fig.update_traces(hovertemplate=metric_string2)
    fig.update_layout(title={"x":.5,"xanchor":"center"},font={"size":16,"color":"#7FDBFF"})
    return fig







#############      TO UPDATE THE US MAP        ################

###### Defining Our Callback Function
@app.callback(Output("fig2","figure"),
    Input("dropdown2","value"))

###### Defining the Action Function
def update_map(metric):
    color_max=1.2*states[title_mappings[metric]].max() # finding max value for the color map
    fig2=px.choropleth(states,geojson=states.geometry,locations=states.STUSPS,locationmode="USA-states",
    scope="usa",hover_name=states.STUSPS,template="plotly_dark",color=title_mappings[metric],
    color_continuous_scale=color_mappings[metric],
    title="National View: "+metric,range_color=[0, color_max])
    fig2.update_layout(title={"x":.5,"xanchor":"center"},font={"size":16,"color":"#7FDBFF"})
    #hover_string=eval('print("Date: %{x} <br>"+metric_string+": %{y}")')
    return fig2



#@app.callback(Output("fig","figure"),
#    Input("dropdown","value"),
# Input("dropdown2","value"))

#def update_series(state,metric):
#    metric_string='%s' %title_mappings[metric]
#    metric_string2="Date: %{x} <br>"+metric_string+": %{y}"
#    fig1=px.line(real_estate_df[real_estate_df["StateName"] == state],x="Date",y=title_mappings[metric],line_group="RegionName",
#    color="RegionName",template="plotly_dark",  #width=800, height=600,
#    hover_name="RegionName",hover_data={"RegionName":False},title="Recorded Cities in "+state,markers="-o")
#    fig1.update_traces(hovertemplate=metric_string2)
#    fig1.update_layout(title={"x":.5,"xanchor":"center"},font={"size":16,"color":"#7FDBFF"})
#    return fig





#    selector_map=


#####    RUNNING THE APPLICATION LOCALLY    #######
if __name__ == '__main__':
    app.run_server(debug =True, port=8086)
