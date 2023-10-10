import pandas as pd 
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.io as pio
import geopandas as gpd
import secrets
import string
import folium
from millify import millify
from shapely import wkt
from shapely.geometry import shape
from streamlit_folium import folium_static
from geopy.distance import great_circle

@st.cache_data
def carregar_municipios_sertao():
    all_muns = pd.read_csv(r"C:/Users/User/Documents/GitHub/BCG2023/Dados/Tabela_final/tabela_final.csv")
    return all_muns

@st.cache_data
def carregar_municipios_potenciais():
    top_muns = pd.read_csv(r"C:/Users/User/Documents/GitHub/BCG2023/Dados/Tabela_final/municipios_potenciais.csv").drop(columns='Unnamed: 0')
    return top_muns

@st.cache_data
def carregar_agro():
    agro = pd.read_csv(r"C:/Users/User/Documents/GitHub/BCG2023/Dados/Tabela_final/dados_producao_agricola.csv").drop(columns='Unnamed: 0')
    return agro

@st.cache_data
def carregar_solos(mun_ser):
    solos = pd.read_csv(r"C:/Users/User/Documents/GitHub/BCG2023/Dados/Views/solos_municipios.csv").drop(columns='Unnamed: 0')
    solos = mun_ser.drop(columns=['LATITUDE', 'LONGITUDE']).merge(solos, on = 'IBGE7').drop(columns=['IBGE7', 'UF'])
    solos['AREA_TOTAL'] = round(solos['AREA_TOTAL'],2)
    return solos

@st.cache_data
def carregar_mapa(top_muns):
    cod_mun = top_muns[['IBGE7','NOME']]
    lim_muns = pd.read_json(r'C:/Users/User/Documents/GitHub/BCG2023/Dados/Views/municipios-poligonos.json')
    lim_muns['poligono'] = [str(polygon) for polygon in lim_muns['poligono']]
    lim_muns['geometry'] = lim_muns['poligono'].apply(lambda x: shape(eval(x)))
    lim_muns = lim_muns[['municipioCodigo', 'geometry']]
    lim_muns.columns = ['IBGE7', 'geometry']
    lim_muns = cod_mun.merge(lim_muns, on = 'IBGE7', how = 'inner')
    lim_muns = gpd.GeoDataFrame(lim_muns, geometry='geometry')
    lim_muns = lim_muns.set_crs("EPSG:4326")
    return lim_muns

@st.cache_data
def carregar_distancia_capital():
    dist = pd.read_csv(r'C:/Users/User/Documents/GitHub/BCG2023/Dados/Views/distancia_capitais.csv')
    return dist

@st.cache_data
def muns_prox(top_muns, mun_ser, raio):
    muns_prox = {}
    for _, row_top in top_muns.iterrows():
        municipio_interesse = row_top['NOME']  
        coordenadas_interesse = (row_top['LATITUDE'], row_top['LONGITUDE'])
        municipios_proximos = {}
        for _, row_ser in mun_ser.iterrows():
            coordenadas_ser = (row_ser['LATITUDE'], row_ser['LONGITUDE'])
            distancia = great_circle(coordenadas_interesse, coordenadas_ser).kilometers
            if distancia <= raio:
                municipios_proximos[row_ser['NOME']] = round(distancia,2)
        muns_prox[municipio_interesse] = municipios_proximos
    return muns_prox

@st.cache_data
def comp_df(top_muns, raio, mun, metric):
    mun_metric = mun_df[metric].iloc[0]
    muns_prox_df = mun_ser[metric].loc[mun_ser['NOME'].isin(list(muns_prox.keys()))].mean()
    comp_df = pd.DataFrame()
    comp_df.insert(0, 'NOME', ['Município Potencial', 'Média do Entorno'])
    comp_df.insert(1, metric, [round(mun_metric,1), round(muns_prox_df,1)])
    return comp_df

def atividades_agricolas(nome_mun):
    atv_agr = agro[agro['NOME']==nome_mun]
    atv_agr = atv_agr[['PRODUTO', 'AREA_PLANTADA', 'VALOR_PROD']].groupby('PRODUTO').sum().reset_index()
    atv_agr = atv_agr.sort_values(by='VALOR_PROD', ascending = False)
    atv_agr['REND_AREA'] = atv_agr['VALOR_PROD']/atv_agr['AREA_PLANTADA']
    atv_agr = round(atv_agr,2)
    return atv_agr.reset_index().drop(columns='index')

def tipos_de_solo(solos, nome_mun):
    solos_prox = solos[solos['NOME']==nome_mun].drop(columns=['NOME'])
    solos_prox = solos_prox.groupby('SOLO').sum().reset_index().sort_values(by='AREA_TOTAL', ascending = False)
    return solos_prox.reset_index().drop(columns='index')

def generate_random_key(length=16):
    characters = string.ascii_letters + string.digits
    random_key = ''.join(secrets.choice(characters) for _ in range(length))
    return random_key

def bar_plot(df, x, y, title, leg_x, leg_y, text):
    df = df.sort_values(by=x)
    fig = px.bar(df, x=x, y=y, orientation='h', text = text)
    fig.update_xaxes(title_text=leg_x)
    fig.update_yaxes(title_text=leg_y)
    fig.update_layout(title=title)
    st.plotly_chart(fig, use_container_width=True)

dist = carregar_distancia_capital()
top_muns = carregar_municipios_potenciais()
top_muns = top_muns.merge(dist, on = 'IBGE7', how = 'inner')
mun_ser = carregar_municipios_sertao()
agro = carregar_agro()
solos = carregar_solos(mun_ser)
lim_muns = carregar_mapa(top_muns)

st.subheader("Município potencial")
col1, col2, col3 = st.columns([2,1,3])
with col1:
    mun = st.selectbox('Município selecionado', top_muns['NOME'].unique())
    mun_df = top_muns[top_muns['NOME']==mun]
    uf = mun_df['UF'].iloc[0]
    pop_tot = millify(mun_df['POP_TOT'], precision=1, drop_nulls=False)
    pop_tot_30 = millify(mun_df['POP_TOT_30KM'], precision=1, drop_nulls=False)
    dist_capital = millify(mun_df['DIST_CAPITAL'], precision=0, drop_nulls=False)
    st.metric('Estado', f"{uf}")
    st.metric('População', pop_tot)
    st.metric('População em um raio de 30Km', pop_tot_30)
    st.metric('Distância para a capital mais próxima', f"{dist_capital} Km")
with col2:
    pass
with col3:
    maps = lim_muns[lim_muns['NOME']==mun]
    m = folium.Map(location=[maps.centroid.y, maps.centroid.x], zoom_start=8.5)
    folium.GeoJson(maps).add_to(m)
    folium_static(m, width=500, height = 400)

st.subheader("Indicadores socioeconômicos")
col1, col2, col3= st.columns(3)
with col1:
    idh = millify(mun_df['IDHM'], precision=3, drop_nulls=False)
    renda = millify(float(mun_df['RDPC']), precision=2, drop_nulls=False)
    st.metric('IDH', idh)
    st.metric('Renda per capita', f"R$ {renda}")
with col2:
    t_analf = round(float(mun_df['T_ANALF15M']),2)
    i_freq = round(float(mun_df['I_FREQ_PROP'])*100,2)
    st.metric('Subíndice de frequência escolar', f"{i_freq} %")
    st.metric('Taxa de analfabetismo (acima de 15 anos)', f"{t_analf} %")
    
with col3:
    desocup = float(mun_df['T_DES18M'])
    pind = float(mun_df['PIND'])
    st.metric('Taxa de desocupação (acima de 18 anos)', f"{desocup} %")
    st.metric('Percentual de extramemente pobres', f"{pind} %")   

st.subheader("Análise comparativa do entorno")
with st.container():
    col1, col2, col3 = st.columns([2,1,3])
    with col1:
        raio = st.select_slider(
            'Raio de distância',
            options=[30, 50, 70, 100],

            format_func = lambda x: str(x)+" Km")

    muns_prox = muns_prox(top_muns, mun_ser, raio)
    muns_prox = muns_prox[mun]

    col1, col2 = st.columns(2)
    with col1:
        bar_plot(
            df = comp_df(top_muns, raio, mun, 'TEMP_MED').sort_values(by='NOME'), 
            x = 'TEMP_MED', 
            y = 'NOME', 
            title = 'Temperatura média anual', 
            leg_x = 'Temperatura média anual (C)',
            leg_y = None ,
            text = 'TEMP_MED'
            )
        bar_plot(
            df = comp_df(top_muns, raio, mun, 'PREC_MED').sort_values(by='NOME'), 
            x = 'PREC_MED', 
            y = 'NOME', 
            title = 'Precipitação média anual', 
            leg_x = 'Precipitação média anual (mm)',
            leg_y = None ,
            text = 'PREC_MED'
            )
        bar_plot(
            df = comp_df(top_muns, raio, mun, 'QUAL_MED_AGUA').sort_values(by='NOME'), 
            x = 'QUAL_MED_AGUA', 
            y = 'NOME', 
            title = 'Índice de qualidade média da água', 
            leg_x = 'Índice de qualidade média da água',
            leg_y = None ,
            text = 'QUAL_MED_AGUA'
            )
    with col2:
        bar_plot(
            df = comp_df(top_muns, raio, mun, 'AREA_IRRIGADA_TOT').sort_values(by='NOME'), 
            x = 'AREA_IRRIGADA_TOT', 
            y = 'NOME', 
            title = 'Área irrigada', 
            leg_x = 'Área irrigada (ha)',
            leg_y = None ,
            text = 'AREA_IRRIGADA_TOT'
            )
        bar_plot(
            df = comp_df(top_muns, raio, mun, 'AREA_IRRIGADA_POT_E').sort_values(by='NOME'), 
            x = 'AREA_IRRIGADA_POT_E', 
            y = 'NOME', 
            title = 'Área adicional irrigada potencial efetiva', 
            leg_x = 'AAI potencial efetiva (ha)',
            leg_y = None ,
            text = 'AREA_IRRIGADA_POT_E'
            )
        bar_plot(
            df = comp_df(top_muns, raio, mun, 'DIST_CORPO_AGUA').sort_values(by='NOME'), 
            x = 'DIST_CORPO_AGUA', 
            y = 'NOME', 
            title = "Distância para o corpo d'água mais próximo", 
            leg_x = "Dist. para o corpo d'água mais próximo (Km)",
            leg_y = None ,
            text = 'DIST_CORPO_AGUA'
            )
        