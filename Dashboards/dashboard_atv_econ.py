# Imports
import secrets
import string
import folium
import branca
import pandas as pd 
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.io as pio
import geopandas as gpd
import plotly.graph_objs as go
from millify import millify
from shapely import wkt
from shapely.geometry import shape
from streamlit_folium import folium_static
from geopy.distance import great_circle
from plotly.subplots import make_subplots

# Funções
@st.cache_data
def carregar_municipios_sertao():
    all_muns = pd.read_csv(r"C:/Users/User/Documents/GitHub/BCG2023/Dados/Tabela_final/municipios_clusters.csv")
    lim_muns = pd.read_json(r'C:/Users/User/Documents/GitHub/BCG2023/Dados/Views/municipios-poligonos.json')
    lim_muns['poligono'] = [str(polygon) for polygon in lim_muns['poligono']]
    lim_muns['geometry'] = lim_muns['poligono'].apply(lambda x: shape(eval(x)))
    lim_muns = lim_muns[['municipioCodigo', 'geometry']].rename(columns={'municipioCodigo':'IBGE7'})
    all_muns = all_muns.merge(lim_muns, on = 'IBGE7', how = 'inner')
    all_muns = gpd.GeoDataFrame(all_muns, geometry='geometry')
    all_muns = all_muns.set_crs("EPSG:4326")
    return all_muns

@st.cache_data
def carregar_agro():
    agro = pd.read_csv(r"C:/Users/User/Documents/GitHub/BCG2023/Dados/Tabela_final/dados_producao_agricola.csv").drop(columns='Unnamed: 0')
    return agro

@st.cache_data
def carregar_solos(_all_muns):
    solos = pd.read_csv(r"C:/Users/User/Documents/GitHub/BCG2023/Dados/Views/solos_municipios.csv").drop(columns='Unnamed: 0')
    solos = _all_muns[['IBGE7', 'NOME']].merge(solos, on = 'IBGE7', how = 'inner').drop(columns='IBGE7')
    solos['AREA_TOTAL'] = round(solos['AREA_TOTAL'],2)
    return solos

def muns_prox(_mun_df, _all_muns, _raio):
    coordenadas_mun = (_mun_df['LATITUDE'].iloc[0], _mun_df['LONGITUDE'].iloc[0])
    muns_prox = {}
    for _, row in _all_muns.iterrows():
        coordenadas_muns_prox = (row['LATITUDE'], row['LONGITUDE'])
        distancia = great_circle(coordenadas_mun, coordenadas_muns_prox).kilometers
        if distancia <= _raio:
            muns_prox[row['NOME']] = round(distancia,2)
    return muns_prox

def comp_df(_metric, _mun_df, _all_muns, _muns_prox_names):
    mun_metric = _mun_df[_metric].iloc[0]
    muns_prox_df = _all_muns[_metric].loc[_all_muns['NOME'].isin(_muns_prox_names)].mean()
    comp_df = pd.DataFrame()
    comp_df.insert(0, 'NOME', ['Município Potencial', 'Média do Entorno'])
    comp_df.insert(1, _metric, [round(mun_metric,1), round(muns_prox_df,1)])
    return comp_df

def agro_comp(agro, mun_name, metric, muns_prox_names):
    if metric in ['VALOR_PROD', 'AREA_PLANTADA']:
        agro_mun = agro[['PRODUTO', metric]].loc[agro['NOME']==mun_name]
        agro_mun = agro_mun.groupby('PRODUTO').sum().reset_index()
        agro_mun[metric] = round(agro_mun[metric],2)
        agro_mun = agro_mun.sort_values(by=metric)
        agro_prox = agro[['PRODUTO', metric]].loc[agro['NOME'].isin(muns_prox_names)]
        agro_prox = agro_prox.groupby('PRODUTO').sum().reset_index()
        agro_prox[metric] = round(agro_prox[metric],2)
        agro_prox = agro_prox.sort_values(by=metric)

    elif metric == 'REND_AREA':
        agro['REND_AREA'] = agro['VALOR_PROD']/agro['AREA_PLANTADA']
        agro_mun = agro[['PRODUTO', 'REND_AREA']].loc[agro['NOME']==mun_name]
        agro_mun = agro_mun.groupby('PRODUTO').mean().reset_index()
        agro_mun['REND_AREA'] = round(agro_mun['REND_AREA'],2)
        agro_mun = agro_mun.sort_values(by=metric)
        agro_prox = agro[['PRODUTO', 'REND_AREA']].loc[agro['NOME'].isin(muns_prox_names)]
        agro_prox = agro_prox.groupby('PRODUTO').mean().reset_index()
        agro_prox['REND_AREA'] = round(agro_prox['REND_AREA'],2)
        agro_prox = agro_prox.sort_values(by=metric)
    return agro_mun, agro_prox

def tipos_de_solo(solos, nome_mun):
    solos_prox = solos[solos['NOME']==mun_name].drop(columns=['NOME'])
    solos_prox = solos_prox.groupby('SOLO').sum().reset_index().sort_values(by='AREA_TOTAL', ascending = False)
    return solos_prox.reset_index().drop(columns='index')

def generate_random_key(length=16):
    characters = string.ascii_letters + string.digits
    random_key = ''.join(secrets.choice(characters) for _ in range(length))
    return random_key

def bar_plot(df, x, y, title, leg_x, leg_y, text):
    df = df.sort_values(by=x)
    fig = px.bar(
        df, 
        x=x, 
        y=y, 
        orientation='h', 
        text = text,
        color='NOME',
        category_orders={'NOME': ['Município Potencial', 'Média do Entorno']}
        )
    fig.data[0].update(showlegend=False)
    fig.data[1].update(showlegend=False)
    fig.update_xaxes(title_text=leg_x)
    fig.update_yaxes(title_text=leg_y)
    fig.update_layout(title=title)
    st.plotly_chart(fig, use_container_width=True)

# Coleta dos dados
all_muns = carregar_municipios_sertao().drop(columns='Unnamed: 0')
agro = carregar_agro()
solos = carregar_solos(all_muns)

# Filtros
st.header("Filtros")
mun_names = all_muns['NOME'].sort_values(ascending=True)
mun_name = st.selectbox('Município', mun_names)

# Informações geográficas
st.header("Informações geográficas")
mun_df = all_muns[all_muns['NOME']== mun_name]
col1, col2, col3 = st.columns(3)
with col1:
    uf = mun_df['UF'].iloc[0]
    capital_prox = mun_df['CAPITAL_PROXIMA'].iloc[0]
    st.metric('Estado', f"{uf}")
    st.metric('Capital mais próxima', f"{capital_prox}")
with col2:
    custo_transporte = millify(mun_df['TRANSPORT_COST'].iloc[0], precision=2, drop_nulls=False)
    dist_capital = millify(mun_df['DIST_CAPITAL'].iloc[0], precision=0, drop_nulls=False)
    st.metric('Distância para a capital mais próxima', f"{dist_capital} Km")
    st.metric('Custo de transporte para o porto mais próximo', f"R${custo_transporte}")
with col3:
    pop_tot = millify(mun_df['POP_TOT'].iloc[0], precision=1, drop_nulls=False)
    pop_tot_30 = millify(mun_df['POP_TOT_30KM'].iloc[0], precision=1, drop_nulls=False)
    st.metric('População', pop_tot)
    st.metric('População em um raio de 30Km', pop_tot_30)

# Indicadores socioeconômicos
st.header("Indicadores socioeconômicos")
col1, col2, col3= st.columns(3)
with col1:
    idh = millify(mun_df['IDHM'].iloc[0], precision=3, drop_nulls=False)
    renda = millify(float(mun_df['RDPC'].iloc[0]), precision=2, drop_nulls=False)
    st.metric('IDH', idh)
    st.metric('Renda per capita', f"R$ {renda}")
with col2:
    t_analf = round(float(mun_df['T_ANALF15M'].iloc[0]),2)
    i_freq = round(float(mun_df['I_FREQ_PROP'].iloc[0])*100,2)
    st.metric('Subíndice de frequência escolar', f"{i_freq} %")
    st.metric('Taxa de analfabetismo (acima de 15 anos)', f"{t_analf} %")
with col3:
    desocup = millify(mun_df['T_DES18M'].iloc[0], precision=1, drop_nulls=False)
    pind = millify(mun_df['PIND'].iloc[0], precision=1, drop_nulls=False)
    st.metric('Taxa de desocupação (acima de 18 anos)', f"{desocup} %")
    st.metric('Percentual de extramemente pobres', f"{pind} %")   

# Análise comparativa
def mudar_tipo_comparacao():
    st.session_state.tipo_comparacao = tipo_comparacao

def mudar_proximidade():
    st.session_state.proximidade = proximidade

def mudar_raio():
    st.session_state.raio = raio

def mudar_vizinhos():
    st.session_state.vizinhos = vizinhos

def mudar_nomes_municipios_comp():
    st.session_state.muns_comp_names = muns_comp_names

if "tipo_comparacao" not in st.session_state:
    st.session_state.tipo_comparacao = 'Vizinhos mais próximos'

if "proximidade" not in st.session_state:
    st.session_state.proximidade = 'Distância geográfica'

if "raio" not in st.session_state:
    st.session_state.raio = '50 Km'

if "vizinhos" not in st.session_state:
    st.session_state.vizinhos = '5'

if "muns_comp_names" not in st.session_state:
    muns_comp_names = [nome for nome in mun_names if nome != mun_name]
    st.session_state.muns_comp_names = muns_comp_names

st.header("Análise comparativa")

tipo_comparacao = st.selectbox(
    'Tipo de comparação', [
        'Vizinhos mais próximos', 
        'Município específico'
        ], 
    on_change = mudar_tipo_comparacao
    )

if tipo_comparacao == 'Vizinhos mais próximos':

    proximidade = st.selectbox(
        'Critério de proximidade', [
            'Distância geográfica', 
            'Características ambientais'
            ],
        on_change = mudar_proximidade)

    if proximidade == 'Distância geográfica':

        raio = st.selectbox(
            'Raio de distância', 
            [50, 70, 100], 
            on_change = mudar_raio
            )
        muns_prox_dict = muns_prox(mun_df, all_muns, raio)
        muns_prox_names = [nome for nome in list(muns_prox_dict.keys()) if nome != mun_df['NOME'].iloc[0]]
    else:
        pass
else:
    muns_comp_names = [nome for nome in mun_names if nome != mun_name]
    mun_comparacao = st.selectbox('Municipio de comparação', muns_comp_names)
    mudar_nomes_municipios_comp()
    muns_prox_names = [mun_comparacao]

st.subheader("Mapa")

def mudar_tipo_de_metrica():
    st.session_state.tipo_metrica = tipo_metrica

def mudar_metrica():
    st.session_state.metrica = metrica

if "tipo_metrica" not in st.session_state:
    st.session_state.tipo_metrica = 'Recursos hídricos'

if "metrica" not in st.session_state:
    st.session_state.metrica = 'Precipitação média anual'

tipo_metrica = st.selectbox(
    'Tipo de métrica', [
        'Recursos hídricos', 
        'Produtos Agrícolas - Valor Comercializado', 
        'Tipos de solo - Área Total'
        ], 
        on_change = mudar_tipo_de_metrica
        )

if tipo_metrica == 'Recursos hídricos':

    aliases = {
        "Distância para o corpo d'água mais próximo (Km)":'DIST_CORPO_AGUA',
        "Precipitação média anual (mm)":'PREC_MED',
        "Temperatura média diária":'TEMP_MED',
    }

    metrica = st.selectbox(
        'Métrica', [
            "Distância para o corpo d'água mais próximo (Km)", 
            "Precipitação média anual (mm)"
            ],
            on_change = mudar_metrica
            )
    metrica_alias = metrica
    metrica =  aliases[metrica_alias]
    
elif tipo_metrica == 'Produtos Agrícolas - Valor Comercializado':
    metrica = st.selectbox(
        'Produto Agrícola', 
        agro['PRODUTO'].unique(),
        on_change = mudar_metrica
        )
else:
    metrica = st.selectbox(
        'Tipo de Solo - Área Total', 
        solos['SOLO'].unique(),
        on_change = mudar_metrica
        )

metrica_alias = "Distância para o corpo d'água mais próximo (Km)"
metrica = 'DIST_CORPO_AGUA'

centroids = all_muns[['NOME', 'geometry']].copy()
centroids.crs = 'epsg:32724'

colormap = branca.colormap.LinearColormap(
    vmin=all_muns[metrica].quantile(0.0),
    vmax=all_muns[metrica].quantile(1),
    colors=[
        "red",
        "orange",
        "yellow",
        "green", 
        "blue",
        "purple"
    ],
    caption=metrica_alias)
    
m = folium.Map(
    location=[
        centroids[centroids['NOME']==mun_name].centroid.values[0].y, 
        centroids[centroids['NOME']==mun_name].centroid.values[0].x
    ], 
    zoom_start=8.5
)

tooltip = folium.GeoJsonTooltip(
    fields=["IBGE7", "NOME", metrica],
    aliases=["Código do IBGE:", "Nome:", f"{metrica_alias}:"],
    localize=True,
    sticky=False,
    labels=True,
    style="""
        background-color: #F0EFEF;
    """,
    max_width=800,
)

g = folium.GeoJson(
    all_muns,
    style_function=lambda x: {
        "fillColor": colormap(x["properties"][metrica])
        if x["properties"][metrica] is not None
        else "transparent",
        "color": "black",
        "fillOpacity": 0.4,
    },
    tooltip=tooltip,
).add_to(m)

folium.Marker(
        location=[
            centroids[centroids['NOME']==mun_name].centroid.values[0].y, 
            centroids[centroids['NOME']==mun_name].centroid.values[0].x
        ],
        icon = folium.Icon(color = 'red')
    ).add_to(m)

for nome in list(muns_prox_names):    
    folium.Marker(
        location=[
            centroids[centroids['NOME']==nome].centroid.values[0].y, 
            centroids[centroids['NOME']==nome].centroid.values[0].x
        ],
        icon = folium.Icon(color = 'blue')
    ).add_to(m)

colormap.add_to(m)

folium_static(m, width = 1200)

# Recursos hídricos
st.subheader("Dados meteorológicos")
col1, col2 = st.columns(2)
with col1:
    bar_plot(
        df = comp_df('PREC_MED', mun_df, all_muns, muns_prox_names), 
        x = 'PREC_MED', 
        y = 'NOME', 
        title = 'Precipitação média anual', 
        leg_x = 'Precipitação média anual (mm)',
        leg_y = None ,
        text = 'PREC_MED'
        )
with col2:
    bar_plot(
        df = comp_df('RED_MED', mun_df, all_muns, muns_prox_names), 
        x = 'RED_MED', 
        y = 'NOME', 
        title = 'Radiação média global', 
        leg_x = 'Radiação média global (Kj/m²)',
        leg_y = None ,
        text = 'RED_MED'
        )

st.subheader("Recursos hídricos")
col1, col2 = st.columns(2)
with col1:
    bar_plot(
        df = comp_df('AREA_IRRIGADA_TOT_POT_E', mun_df, all_muns, muns_prox_names), 
        x = 'AREA_IRRIGADA_TOT_POT_E', 
        y = 'NOME', 
        title = 'Área irrigada total e potencial efetiva', 
        leg_x = 'Área irrigada (ha)',
        leg_y = None ,
        text = 'AREA_IRRIGADA_TOT_POT_E'
        )
with col2:
    bar_plot(
        df = comp_df('QUAL_MED_AGUA', mun_df, all_muns, muns_prox_names), 
        x = 'QUAL_MED_AGUA', 
        y = 'NOME', 
        title = 'Índice de qualidade média da água', 
        leg_x = 'Índice de qualidade média da água',
        leg_y = None ,
        text = 'QUAL_MED_AGUA'
        )
# Atividades agrícolas
st.subheader("Atividades agrícolas")   
agro_mun, agro_prox = agro_comp(agro, mun_name, 'VALOR_PROD', muns_prox_names)
fig = make_subplots(rows=1, cols=2, subplot_titles=('Município potencial', 'Total do entorno'))
trace1 = px.bar(
    agro_mun,
    x='VALOR_PROD',
        y='PRODUTO',
    orientation='h'
)
fig.add_trace(trace1.data[0], row=1, col=1)

trace2 = px.bar(
    agro_prox,
     x='VALOR_PROD',
    y='PRODUTO',
    orientation='h',
)
fig.add_trace(trace2.data[0], row=1, col=2)

fig.update_layout(
    title='Produtos agrícolas mais comercializados',
    yaxis=dict(title='Produtos'),
    xaxis=dict(title='Valor comercializado (R$)')
)

st.plotly_chart(fig, use_container_width=True)

agro_mun, agro_prox = agro_comp(agro, mun_name, 'AREA_PLANTADA', muns_prox_names)
fig = make_subplots(rows=1, cols=2, subplot_titles=('Município potencial', 'Total do entorno'))
trace1 = px.bar(
    agro_mun,
    x='AREA_PLANTADA',
    y='PRODUTO',
    orientation='h'
)
fig.add_trace(trace1.data[0], row=1, col=1)

trace2 = px.bar(
    agro_prox,
    x='AREA_PLANTADA',
    y='PRODUTO',
    orientation='h'
)
fig.add_trace(trace2.data[0], row=1, col=2)

fig.update_layout(
    title='Produtos agrícolas com maior área plantada',
    yaxis=dict(title='Produtos'),
    xaxis=dict(title='Área plantada (ha)')
)

st.plotly_chart(fig, use_container_width=True)

agro_mun, agro_prox = agro_comp(agro, mun_name, 'REND_AREA', muns_prox_names)
fig = make_subplots(rows=1, cols=2, subplot_titles=('Município potencial', 'Média do entorno'))
trace1 = px.bar(
    agro_mun,
    x='REND_AREA',
    y='PRODUTO',
    orientation='h'
)
fig.add_trace(trace1.data[0], row=1, col=1)

trace2 = px.bar(
    agro_prox,
    x='REND_AREA',
    y='PRODUTO',
    orientation='h'
)
fig.add_trace(trace2.data[0], row=1, col=2)

fig.update_layout(
    title='Produtos agrícolas com maior rendimento por área plantada',
    yaxis=dict(title='Produtos'),
    xaxis=dict(title='Valor comercializado (R$) / Área plantada (ha)')
)

st.plotly_chart(fig, use_container_width=True)

# Tipos de solos
st.subheader("Solos")
solos_mun = solos[['SOLO', 'AREA_TOTAL']].loc[solos['NOME']==mun_name].sort_values(by='AREA_TOTAL')
solos_prox = solos[solos['NOME'].isin(list(muns_prox_names))]
solos_prox = solos_prox[['SOLO', 'AREA_TOTAL']].groupby('SOLO').sum().reset_index().sort_values(by='AREA_TOTAL')

fig = make_subplots(
    rows=1, 
    cols=2, 
    subplot_titles=('Município potencial', 'Total do entorno'),
    horizontal_spacing = 0.3
    )
trace1 = px.bar(
    solos_mun,
    x='AREA_TOTAL',
    y='SOLO',
    orientation='h'
)
fig.add_trace(trace1.data[0], row=1, col=1)

trace2 = px.bar(
    solos_prox,
    x='AREA_TOTAL',
    y='SOLO',
    orientation='h'
)
fig.add_trace(trace2.data[0], row=1, col=2)

fig.update_layout(
    title='Tipos de solos mais comuns',
    yaxis=dict(title='Solos'),
    xaxis=dict(title='Área total (ha)')
)

st.plotly_chart(fig, use_container_width=True)