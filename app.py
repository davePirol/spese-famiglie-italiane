from dash import Dash, html, dcc, Input, Output  # pip install dash
import plotly.express as px
import dash_bootstrap_components as dbc          # pip install dash-bootstrap-components
import pandas as pd                              # pip install pandas

import matplotlib                                # pip install matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np 
import textwrap

#DATA PREPARATION
#spese.csv
df = pd.read_csv("spese.csv", quotechar="'")
selected_columns = ['Territorio', 'COICOP', 'Coicop (DESC)', 'componenti', 'Anno', 'Spesa media']
df = df[selected_columns]

#spesa media
df['Spesa media'] = pd.to_numeric(df['Spesa media'], errors='coerce')
df['Spesa media'] = df['Spesa media'].replace(np.nan, -1, regex=True)
df['Spesa media'] = df['Spesa media'].astype(float)
df = df[df['Spesa media'] >= 0]

#territorio
df.replace(inplace=True, to_replace='Valle d"Aosta / Vallée d"\'Aoste\'', value='Valle d\'Aosta/Vallée d\'Aoste')
df.replace(inplace=True, to_replace='Trentino Alto Adige / Südtirol', value='Trentino-Alto Adige/Südtirol')
regioni=df['Territorio'].unique()
regioni.sort()

#categorie
values_to_exclude = ['0220', '0461_MANUT_STR', '0520', '0540', '0630', '0810', '0820', '0830', '0960', '1010', '1020', '1030', '1040', '1050', '1120', '1240', '1262', '1270']
df = df[~df['COICOP'].isin(values_to_exclude)]
df.loc[df['COICOP'] == '046_MANUT_STR', 'COICOP'] = '046'

#root
df.loc[df['COICOP'] == 'NON_FOOD', 'Root'] = 'Non alimenti'
df.loc[((df['COICOP'].str.len() == 2)) | (df['COICOP'] == 'ALL'), 'Root'] = df['Coicop (DESC)']

##first level
df.loc[((df['COICOP'].str.len() == 3) & (df['Root'].isna())), 'First_level'] = df['Coicop (DESC)']

##second level
df.loc[((df['COICOP'].str.len() == 4) & (df['First_level'].isna()) & (df['Root'].isna())), 'Second_level'] = df['Coicop (DESC)']

#fill the gaps
mask = df['Root'].isna()
df['Root'] = df['Root'].fillna(method='ffill')
df.loc[mask, 'First_level'] = df['First_level'].fillna(method='ffill')

macro_category=df[df['First_level'].isna() & df['Second_level'].isna()]['Coicop (DESC)'].unique()

#spesa media
df['Spesa media'] = pd.to_numeric(df['Spesa media'], errors='coerce')
df['Spesa media'] = df['Spesa media'].replace(np.nan, -1, regex=True)
df['Spesa media'] = df['Spesa media'].astype(float)
df = df[df['Spesa media'] >= 0]

#famiglie.csv
df2 = pd.read_csv("famiglie.csv", quotechar="'")
selected_columns_famiglia =['Territorio', 'COICOP', 'Coicop (DESC)', 'Anno', 'Spesa media', 'Tipologia famigliare']
df2 = df2[selected_columns_famiglia]

#spesa media
df2['Spesa media'] = pd.to_numeric(df2['Spesa media'], errors='coerce')
df2['Spesa media'] = df2['Spesa media'].replace(np.nan, -1, regex=True)
df2['Spesa media'] = df2['Spesa media'].astype(float)
df2 = df2[df2['Spesa media'] >= 0]

#categorie
#root
df2.loc[df2['COICOP'] == 'NON_FOOD', 'Root'] = 'Non alimentari'
df2.loc[((df2['COICOP'].str.len() == 2)) | (df2['COICOP'] == 'ALL'), 'Root'] = df2['Coicop (DESC)']

##first level
df2.loc[((df2['COICOP'].str.len() == 4) & (df2['Root'].isna())), 'First_level'] = df2['Coicop (DESC)']

#fill the gaps
df2['Root'] = df2['Root'].fillna(method='ffill')
macro_category_family=df2[df2['First_level'].isna()]['Coicop (DESC)'].unique()


#function to change the slider values
def change_slider_value_territory(territory):
    
    if(territory=='Italia'):
        result= dcc.Slider(
                        df['Anno'].min(),
                        df['Anno'].max(),
                        value=df['Anno'].min(),
                        marks={i: '{}'.format(i) for i in range(df['Anno'].min(), df['Anno'].max()+1)},
                        step=1,
                        id='anno-list-hist-grouped'
                    )
    else:
        result= dcc.Slider(
                        2014,
                        df['Anno'].max(),
                        value=2014,
                        marks={i: '{}'.format(i) for i in range(2014, df['Anno'].max()+1)},
                        step=1,
                        id='anno-list-hist-grouped'
                    )
    return result

def generate_heat_map():
    mask = df2[(df2['Territorio']=='Italia') & (df2['Coicop (DESC)'].isin(macro_category_family)) & (~df2['Coicop (DESC)'].isin(['Totale']))].groupby(
    ['Anno', 'Coicop (DESC)', 'Tipologia famigliare']).mean('Spesa media')

    heatmap_data = mask.pivot_table(
        index='Coicop (DESC)', 
        columns='Tipologia famigliare', 
        values='Spesa media', 
        aggfunc='mean'
    ).fillna(0)  
    fig = px.imshow(
        heatmap_data,
        labels=dict(
            x="Tipologia famigliare", 
            y="Categoria di spesa", 
            color="Spesa media"),
        x=heatmap_data.columns,
        y=heatmap_data.index,
        color_continuous_scale="burgyl",
    )

    fig.update_layout(
        autosize=False,
        width=1200,  
        height=800   
    )

    fig.update_layout(
        legend=dict(
            x=3,  # The x position of the legend (1 is the far right)
            y=1,  # The y position of the legend (1 is the top)
            xanchor='right',  # Anchor point for the x position
            yanchor='top',    # Anchor point for the y position
            tracegroupgap=5,  # Space between trace groups in legend
            itemwidth=30,     # The width of legend items (symbols)
            itemsizing='trace'  # Controls if the legend items symbols scale with their corresponding trace
        )
    )

    
    return dcc.Graph(figure=fig)

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = html.Div([
    dbc.Container([
        html.Div([
            html.H1("Spese annuali delle famiglie italiane", className='mb-2', style={'textAlign':'center'}),
            html.P("Tutti i dati delle spese si riferiscono alla spesa mensile del nucleo familiare espressi in euro", className='mb-2', style={'textAlign':'center', 'font-style':'italic'}),
            html.P("I grafici riportati mostrano la spesa mensile delle famiglie residenti in Italia. "+
                   "I dati sono stati raccolti dalla banca dati dell'ISTAT. "+
                   "Vengono riportati diversi grafici multidimensionali per mostrare nel modo più adeguato ed espressivo:", className='mb-2', style={'font-style':'bold'}),
            html.Ul([
                html.Li("Il trend negli anni delle spese"),
                html.Li("La relazione tra le spese e il nucleo famigliare"),
                html.Li("Le spese in base alle categorie e sotto categorie"),
                html.Li("Le spese in base alla regione e macro regione di residenza delle famiglie"),
            ]),
            html.P("Sono stati analizzati due dataset, il primo, descritto dai primi quattro grafici che raccoglie i dati di spesa relativi"+
                   " alle regioni e alle categorie di spesa nel dettaglio. Il secondo, descritto dagli ultimi quattro grafici, esprime "+
                   "i dati relativi alle spese nelle varie tipologie di nuclei famigliari.", className='mb-2', style={'font-style':'bold'}),
            html.P("L'attributo \"Coicop (DESC)\" (Classification of Individual COnsumption by Purpose, classificazione dei consumi individuali secondo lo scopo)"+
                   " è uno standard internazionale messo a punto dalla Divisione Statistica delle Nazioni Unite. Viene usato per la "+
                   "descrizione del tipo di spesa e se ne individuano 14 capitoli. I primi 12 relativi ai consumi delle famiglie, "+
                   "uno relativo ai consumi individuali delle istituzioni sociali private al servizio delle famiglie, "+
                   "l'ultimo a quelli delle amministrazioni pubbliche (non utilizzato nelle osservazioni sottostanti).", className='mb-2', style={'font-style':'bold'}),
            html.P("L'attributo regione comprende anche le province di Bolzano e Trento, oltre all'intero Trentino alto Adige, "+
                   "ma nella mappa geografica la regione è trattata tutta insieme.", className='mb-2', style={'font-style':'bold'}),

            html.Hr(),
        ], style={"padding": "30px"}),

        html.Div([
            dbc.Row([
                dbc.Col([
                    html.H4("Trend per macro categorie di spesa")
                ], width=12)
            ]),

            dbc.Row([
                dbc.Col([
                    html.P("Territorio"),
                    dcc.Dropdown(
                        id="territorio-list",
                        options=df['Territorio'].unique(),
                        value="Italia",
                        )
                    ], width=6),
                dbc.Col([
                    html.P("Componenti familiari"),
                    dcc.Dropdown(
                        id="componenti-list",
                        options=df['componenti'].unique(),
                        value='1',
                    )], width= 6)
            ], style={"margin-bottom":"10px"}),

            dbc.Row([
                dbc.Col([
                    dcc.Graph(id="year-graph", style={"heigth":"100%"}),
                ], width=6),
                dbc.Col([
                    dcc.Graph(id="year-graph-over", style={"heigth":"100vh"}),
                ], width=6),
            ]),
        ], style={'border': 'solid 3px #F3B95F', 'border-radius': '20px', 'padding': '20px'}),

        html.Div([
            dbc.Row([
                dbc.Col([
                    html.H4("Variazione delle spese rispetto al nucleo familiare")
                ], width=12,className='mt-4')
            ]),

            dbc.Row([
                dbc.Col([
                    html.P("Territorio"),
                    dcc.Dropdown(
                        id="territorio-list-hist-grouped",
                        options=regioni,
                        value="Italia",
                    ),
                ], width= 2),
                dbc.Col([
                    html.P("Anno"),
                    html.Div([
                        dcc.Slider(0,0,id='anno-list-hist-grouped')
                    ],id='dynamic_sliders_territory')
                ], width= 10)
            ]),

            dbc.Row([
                dbc.Col([
                    dcc.Graph(id="category-hist-gruped", style={"heigth":"100vh"}),
                ], width=12),
                
            ]),
        ], style={'border': 'solid 3px #F3B95F', 'border-radius': '20px', 'padding': '20px', 'margin-top': '5%'}),

        html.Div([
            dbc.Row([
                dbc.Col([
                    html.H4("Distribuzione geografica delle spese")
                ], width=12,className='mt-4')
            ]),

            dbc.Row([
                dbc.Col([
                    html.P("Categoria"),
                    dcc.Dropdown(
                        id="category-list-choro",
                        options=macro_category,
                        value= 'Totale'
                    ),
                ], width=6),
                dbc.Col([
                    html.P("Nucleo familiare"),
                    dcc.Dropdown(
                        id="components-list-choro",
                        options=df['componenti'].unique(),
                        value='1',
                    )
                ], width=6),
                dbc.Col([
                    html.P("Anno"),
                    dcc.Slider(
                        2014,
                        df['Anno'].max(),
                        value=2014,
                        marks={i: '{}'.format(i) for i in range(2014, df['Anno'].max()+1)},
                        step=1,
                        id='year-list-choro'
                    )
                ], width=12)
            ], className='mt-4'),

            dbc.Row([
                dbc.Col([
                    dcc.Graph(id="territory-choro", style={'height': '60vh'}),
                ], width=8),
                dbc.Col([
                    dcc.Graph(id="territory-pie", style={'height': '60vh'}),
                ], width= 4)
            ]),
        ], style={'border': 'solid 3px #F3B95F', 'border-radius': '20px', 'padding': '20px', 'margin-top': '5%'}),

        html.Div([
            dbc.Row([
                dbc.Col([
                    html.H4("Distribuzione delle spese in base alla categoria in Italia")
                ], width=12,className='mt-4')
            ]),

            dbc.Row([
                dbc.Col([
                    html.P("Nucleo familiare"),
                    dcc.Dropdown(
                        id="components-list-mosaic",
                        options=df['componenti'].unique(),
                        value='1'
                    ),
                ], width=3),
                dbc.Col([
                    html.P("Anno"),
                    dcc.Slider(
                        2014,
                        df['Anno'].max(),
                        value=2014,
                        marks={i: '{}'.format(i) for i in range(df['Anno'].min(), df['Anno'].max()+1)},
                        step=1,
                        id="year-list-mosaic"
                    ),
                ], width=9)
            ], className='mt-4'),

            dbc.Row([
                dbc.Col([
                    dcc.Tabs(
                        id="tab",
                        value="treemap",
                        children=[
                            dcc.Tab(label="Treemap", value="treemap"),
                            dcc.Tab(label="Sunburst", value="sunburst"),
                        ],
                    ),
                    html.Div(id="tabs-content"),
                ], width=12, className='mt-25')
            ], style={"margin-top": "25px"}),
        ], style={'border': 'solid 3px #F3B95F', 'border-radius': '20px', 'padding': '20px', 'margin-top': '5%'}),


        dbc.Row([
            dbc.Col([
                html.H2("Analisi delle spese dei nuclei famigliari nel dettaglio", style={"text-align": 'center', "margin-top": "10%"})
            ], width=12,className='mt-4')
        ]),

        html.Div([
            dbc.Row([
                dbc.Col([
                    html.H4("Spese per nucleo famigliare di ogni categoria")
                ], width=12,className='mt-4')
            ]),

            dbc.Row([
                dbc.Col([
                   html.P("Tipologia famigliare"),
                   dcc.Dropdown(
                       id='family-list-bar-polar',
                       options=df2['Tipologia famigliare'].unique(),
                       value='Totale famiglie'
                   ) 
                ], width=3),
                dbc.Col([
                    html.P("Anno"),
                    dcc.Slider(
                        df2['Anno'].min(),
                        df2['Anno'].max(),
                        value=df2['Anno'].min(),
                        marks={i: '{}'.format(i) for i in range(df2['Anno'].min(), df2['Anno'].max()+1)},
                        step=1,
                        id="year-list-bar-polar"
                    ),
                ], width=9)
            ], className='mt-4'),

            dbc.Row([
                dbc.Col([
                    dcc.Graph(id="bar-polar-app-x-graph"),
                ], width=12, className='mt-25')
            ], style={"margin-top": "25px"}),


        ], style={'border': 'solid 3px #F3B95F', 'border-radius': '20px', 'padding': '20px', 'margin-top': '5%'}),

        html.Div([
            dbc.Row([
                dbc.Col([
                    html.H4("Trend annuale per ogni tipologia famigliare e per ogni categoria di spesa")
                ], width=12,className='mt-4')
            ]),

            dbc.Row([
                dbc.Col([
                    html.P("Tipologia famigliare"),
                    dcc.Dropdown(
                        id="family-list-line2",
                        options=df2['Tipologia famigliare'].unique(),
                        value='Totale famiglie'
                    ),
                ], width=6),
                dbc.Col([
                    html.P("Categoria di spesa"),
                    dcc.Dropdown(
                        id="category-list-line2",
                        options=df2['Coicop (DESC)'].unique(),
                        value='Totale'
                    ),
                ], width=6)
            ], className='mt-4'),

            dbc.Row([
                dbc.Col([
                    dcc.Graph(id="line2"),
                ], width=12, className='mt-25')
            ], style={"margin-top": "25px"}),


        ], style={'border': 'solid 3px #F3B95F', 'border-radius': '20px', 'padding': '20px', 'margin-top': '5%'}),

        html.Div([
            dbc.Row([
                dbc.Col([
                    html.H4("Spesa media negli anni, tra tipologia familiare e categoria di spesa")
                ], width=12,className='mt-4')
            ]),

            dbc.Row([
                dbc.Col([
                    generate_heat_map(),
                ], width=12, className='mt-25')
            ], style={"margin-top": "25px", "text-align": "center"}),


        ], style={'border': 'solid 3px #F3B95F', 'border-radius': '20px', 'padding': '20px', 'margin-top': '5%'}),

         html.Div([
            dbc.Row([
                dbc.Col([
                    html.H4("Grafico di spesa tra famiglie e categoria di spesa")
                ], width=12,className='mt-4')
            ]),
            dbc.Row([
                dbc.Col([
                    html.P("Macro regione"),
                    dcc.Dropdown(
                        id="territory-list-scatter",
                        options=df2['Territorio'].unique(),
                        value='Italia'
                    ),
                ], width=3),
                dbc.Col([
                    html.P("Anno"),
                    dcc.Slider(
                        df2['Anno'].min(),
                        df2['Anno'].max(),
                        value=df2['Anno'].min(),
                        marks={i: '{}'.format(i) for i in range(df2['Anno'].min(), df2['Anno'].max()+1)},
                        step=1,
                        id="year-list-scatter"
                    ),
                ], width=9)
            ], className='mt-4'),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='scatter'),
                ], width=12, className='mt-25')
            ], style={"margin-top": "25px", "text-align": "center"}),


        ], style={'border': 'solid 3px #F3B95F', 'border-radius': '20px', 'padding': '20px', 'margin-top': '5%'}),

    ], style={"max-width":"95%"}),
    html.Footer([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H4('Disegnato e progettato da Davide Pirolo'),
                    html.P('Università di Pisa. Anno Accademico 2023-2024', style={'font-style':'italic'})
                ], width=5),
                dbc.Col([
                    html.H5('Progetto del corso di Scientific Large Data Visualization'),
                    html.P('Visualizzazione dati relativi alle spese famigliari espressi in euro.'+
                           'Le spese sono calcolate su base mensile sulla media nazionale oppure regionale.'+
                           ''),
                    html.P('Tutti i dati sono raccolti dalla banca dati ISTAT', 
                           style={'font-style':'italic'})
                ], width=7)
            ], style={"padding": "10%"})
        ])
    ], id="foot")
])

@app.callback(
    Output('dynamic_sliders_territory','children'), 
    Input('territorio-list-hist-grouped', 'value')
)
def update_num_sliders(value):
    return html.Div(change_slider_value_territory(value)),


@app.callback(
    Output("year-graph", "figure"), 
    Output("year-graph-over", "figure"), 
    Input("territorio-list", "value"),
    Input("componenti-list", "value"),
)
def update_over_line(region, components):
    macro_without_total= np.delete(macro_category, np.where(macro_category == 'Totale'))
    mask = df[(df['Territorio'] == region) & (df['componenti'] == components) & (df['Coicop (DESC)'].isin(macro_without_total))]
    mask_with_total = df[(df['Territorio'] == region) & (df['componenti'] == components) & (df['Coicop (DESC)'].isin(macro_category))]
   
    fig_line = px.line(mask_with_total, x="Anno", y="Spesa media", color="Coicop (DESC)", )

    area_size = mask.groupby('Coicop (DESC)')['Spesa media'].sum().reset_index()
    sorted_categories = area_size.sort_values('Spesa media', ascending=False)['Coicop (DESC)']
    mask['Coicop (DESC)'] = pd.Categorical(mask['Coicop (DESC)'], categories=sorted_categories, ordered=True)
    mask.sort_values('Coicop (DESC)', inplace=True)

    fig_area = px.area(mask, x="Anno", y='Spesa media', color="Coicop (DESC)", line_group="Coicop (DESC)")
    
    fig_line.update_layout(
        #autosize=True,
        margin=dict(l=30, r=0, t=30, b=30),
        legend=dict(
            y=-0.2,
            xanchor='center',
            yanchor='top',
            orientation='h',
            x=0.5
        ))
    fig_area.update_layout(
        autosize=True,
        margin=dict(l=30, r=0, t=30, b=30),
        legend=dict(
            y=-0.2,
            xanchor='center',
            yanchor='top',
            orientation='h',
            x=0.5
        )
    )

    return fig_line, fig_area

@app.callback(
    Output("category-hist-gruped", "figure"), 
    Input("territorio-list-hist-grouped", "value"),
    Input("anno-list-hist-grouped", "value"),
)
def update_over_line(region, year):
    
    mask = df[(df['Territorio'] == region) & (df['Anno'] == year) & (df['Coicop (DESC)'].isin(macro_category))]
    grouped_data = mask.groupby(['componenti', 'Coicop (DESC)']).agg(spesa_media=('Spesa media', 'mean')).reset_index()
    mean_values = mask.groupby('Coicop (DESC)')['Spesa media'].mean().reset_index()
    
    traces=[]
    fig = go.Figure()
    
    '''for _, mean_row in mean_values.iterrows():
        fig.add_trace(go.Bar(
            x=[mean_row['Coicop (DESC)']], 
            y=[mean_row['Spesa media']],
            name='Media', 
            marker_color='rgba(150, 150, 150, 0.5)', 
            width=1, 
            showlegend=False,
        ))'''
    
    for i, group_df in grouped_data.groupby('componenti'):
        fig.add_trace(go.Bar(
            x=group_df['Coicop (DESC)'], 
            y=group_df['spesa_media'], 
            name=str(i),
        ))
    

    fig.update_layout(
        barmode='group', 
        yaxis_title_text = 'Spesa media', 
        bargroupgap=0.1, 
        bargap=0.2,
        title="Grafico in scala logaritmica" 
    ) 
    fig.update_yaxes(type="log")

    return fig


@app.callback(
    Output("territory-choro", "figure"), 
    Output("territory-pie", "figure"), 
    Input("category-list-choro", "value"),
    Input("year-list-choro", "value"),
    Input("components-list-choro", "value"),
)
def update_over_line(category, year, components):
    mask = df[(df['componenti'] == components) & (df['Anno'] == year) & (df['Coicop (DESC)']==category)]
    macro_region = df[(df['componenti'] == components) & (df['Coicop (DESC)']==category) 
                      & (df['Territorio'].isin(['Nord', 'Mezzogiorno', 'Centro']))].groupby(['Anno', 'Territorio', 'Coicop (DESC)'])['Spesa media'].mean().reset_index()
    
    geojson_italy = 'https://raw.githubusercontent.com/openpolis/geojson-italy/master/geojson/limits_IT_regions.geojson'

    fig = px.choropleth(mask, 
                    geojson=geojson_italy, 
                    locations='Territorio', # name of dataframe column
                    featureidkey='properties.reg_name',  # path to field in GeoJSON feature object with which to match the values passed in to locations
                    color='Spesa media',
                    color_continuous_scale="bluered",
                    scope="europe",
                    labels={'Spesa media':'Spesa media'}
                   )
    
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    bar = px.bar(macro_region, x="Spesa media", y='Anno', orientation='h', color='Territorio',title="Spese negli anni per macro regione")

    bar.update_layout(
        margin=dict(l=100, r=20, t=50, b=5),  
        yaxis=dict(automargin=True),
        bargap=0.5,
        legend=dict(
            y=-0.2,
            xanchor='center',
            yanchor='top',
            orientation='h',
            x=0.5
        )
    )
    ticktexts = [str(year) for year in macro_region['Anno'].unique()]  
    ticktexts = [textwrap.shorten(tick, width=30, placeholder="...") for tick in ticktexts] 

    bar.update_yaxes(tickmode='array', tickvals=macro_region['Anno'].unique(), ticktext=ticktexts)

    return fig, bar


@app.callback(
    Output("tabs-content", "children"),
    Input("year-list-mosaic", "value"),
    Input("tab", "value"),
    Input("components-list-mosaic", "value"),
)
def main_callback_logic(year, tab, components):
    
    mask = df[(df['componenti'] == components) & (df['Anno'] == year) & (df['Territorio']=='Italia')]
    dff = mask.groupby(by=["Root", "First_level", "Second_level", "Coicop (DESC)"]).sum('Spesa media').reset_index()

    if tab == "treemap":
        fig = px.treemap(
            dff, path=[px.Constant("ALL"), "Root", "First_level", "Coicop (DESC)"], 
            values='Spesa media', labels={'id': 'Coicop (DESC)'},
        )
    else:
        fig = px.sunburst(
            dff, path=[px.Constant("ALL"), "Root", "First_level", "Coicop (DESC)"], 
            values='Spesa media', labels={'id': 'Coicop (DESC)'}
        )

    fig.update_traces(root_color="lightgrey")
    fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))

    return dcc.Graph(figure=fig)

@app.callback(
    Output("bar-polar-app-x-graph", "figure"),
    Input("year-list-bar-polar", "value"),
    Input("family-list-bar-polar", "value"),
)
def main_callback_logic(year, family):

    mask = df2[(df2['Anno'] == year) & (df2['Tipologia famigliare']==family) & (df2['Coicop (DESC)'].isin(macro_category_family))]
    sorted_mask = mask.sort_values(by=["Spesa media"], ascending=True)
    territories_sorted_by_spesa = (
        sorted_mask.groupby("Territorio")["Spesa media"].mean().sort_values(ascending=True).index
    )
    fig = px.bar_polar(
        mask,
        r=mask["Spesa media"],
        theta=mask["Coicop (DESC)"],
        color=mask["Territorio"],
        template="plotly_white",
        log_r=True,
        title="Spesa per categoria suddivise in regioni (in scala logaritmica)",
        category_orders={"Territorio": territories_sorted_by_spesa.tolist()}
    )
    return fig
    
@app.callback(
    Output("line2", "figure"),
    Input("category-list-line2", "value"),
    Input("family-list-line2", "value"),
)
def main_callback_logic(categoria, famiglia):
    mask = df2[(df2['Coicop (DESC)']==categoria) & (df2['Tipologia famigliare']==famiglia)]
    fig = px.line(
        mask,
        x="Anno",
        y="Spesa media",
        color="Territorio",
        markers=True,
    )
    fig.update(layout=dict(title=dict(x=0.5)))
    return fig

@app.callback(
    Output("scatter", "figure"),
    Input("year-list-scatter", "value"),
    Input("territory-list-scatter", "value"),
)
def main_callback_logic(year, territory):
    mask = df2[(df2['Anno']==year) &(df2['Territorio']==territory) & (df2['Coicop (DESC)'].isin(macro_category_family)) & (~df2['Coicop (DESC)'].isin(['Totale']))]

    fig=px.scatter(
                mask,
                x="Tipologia famigliare",
                y="Coicop (DESC)",
                size="Spesa media",
                color="Spesa media",
                color_continuous_scale="hot"
            )
    fig.update_layout(
        xaxis={'type': 'category'},  
        yaxis={'type': 'category'}
    )
    return fig

if __name__ == '__main__':
    app.run_server(debug=True, port=8002)