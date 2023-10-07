import pandas as pd 
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.io as pio
import secrets
import string
from millify import millify

@st.cache_data
def carregar_municipios_potenciais():
    top_muns = pd.read_csv(r"C:/Users/User/Documents/GitHub/BCG2023/Dados/Tabela_final/municipios_potenciais.csv").drop(columns='Unnamed: 0')
    return top_muns

@st.cache_data
def carregar_municipios_sertao():
    mun_ser = pd.read_csv(r"C:/Users/User/Documents/GitHub/BCG2023/Dados/Views/municipios_sertao.csv").drop(columns = 'Unnamed: 0')
    return mun_ser

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

def muns_prox(top_muns, raio):
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

top_muns = carregar_municipios_potenciais()
mun_ser = carregar_municipios_sertao()
agro = carregar_agro()
solos = carregar_solos(mun_ser)

col1, col2, col3= st.columns(3)
with col1:
    mun = st.selectbox('Município selecionado', top_muns['NOME'].unique())
    mun_df = top_muns[top_muns['NOME']==mun]

st.subheader("Indicadores socioeconômicos")

col1, col2, col3= st.columns(3)
with col1:
    metric = millify(mun_df['IDHM'], precision=3, drop_nulls=False)
    st.metric('IDH', mun_df['IDHM'])
with col2:
    metric = millify(mun_df['POP_TOT'], precision=1, drop_nulls=False)
    st.metric('População', metric)
with col3:
    metric = millify(mun_df['POP_TOT_30KM'], precision=1, drop_nulls=False)
    st.metric('População em um raio de 30Km', metric)

col1, col2, col3= st.columns(3)
with col1:
    metric = float(mun_df['RDPC'])
    metric = millify(metric, precision=2, drop_nulls=False)
    st.metric('Renda per capita', f"R$ {metric}")
with col2:
    metric = float(mun_df['T_DES18M'])
    st.metric('Taxa de desocupação (acima de 18 anos)', f"{metric} %")
with col3:
    metric = float(mun_df['PIND'])
    st.metric('Percentual de extramemente pobres', f"{metric} %")

col1, col2, col3= st.columns(3)
with col1:
    metric = round(float(mun_df['T_ANALF15M']),2)
    st.metric('Taxa de analfabetismo (acima de 15 anos)', f"{metric} %")
with col2:
    metric = round(float(mun_df['I_FREQ_PROP'])*100,2)
    st.metric('Subíndice de frequência escolar', f"{metric} %")
with col3:
    pass

st.subheader("Indicadores ambientais")

col1, col2, col3= st.columns(3)
with col1:
    metric = round(float(mun_df['PREC_MED']*365),1)
    st.metric('Precipitação média anual', f'{metric} mm')
with col2:
    metric = millify(mun_df['DIST_CORPO_AGUA'], precision=1, drop_nulls=False)
    st.metric("Distância para o corpo d'água mais próximo", f'{metric} Km')
with col3:
    metric = round(float(mun_df['QUAL_MED_AGUA']),1)
    st.metric('Índice de qualidade da água', metric)

col1, col2, col3= st.columns(3)
with col1:
    metric = round(float(mun_df['AREA_IRRIGADA_TOT']),1)
    st.metric('Área irrigada total', f'{metric} ha')
with col2:
    metric = round(float(mun_df['AREA_IRRIGADA_POT_E']),1)
    st.metric('Área adicional irrigada potencial efetiva', f'{metric} ha')
with col3:
    pass

mun_solos = tipos_de_solo(solos, mun)
mun_solos = mun_solos.sort_values(by='AREA_TOTAL')
fig = px.bar(mun_solos, y='SOLO', x='AREA_TOTAL', orientation='h', text = 'AREA_TOTAL')
fig.update_xaxes(title_text='Área total (ha)')
fig.update_yaxes(title_text='Tipo de solo')
fig.update_layout(title='Tipos de solos mais comuns')
st.plotly_chart(fig, theme="streamlit")

st.subheader("Atividades agrícolas")
atv_agr = atividades_agricolas(mun)
col1, col2, col3 = st.columns(3)
with col1:
    bar_plot(
        atv_agr, 
        'AREA_PLANTADA', 
        'PRODUTO', 
        'Produtos agrícolas com maior área plantada', 
        'Área plantada (ha)', 
        'Produto agrícola',
        'AREA_PLANTADA'
        )
with col2:
    bar_plot(
        atv_agr, 
        'VALOR_PROD', 
        'PRODUTO', 
        'Produtos agrícolas com maior valor produzido', 
        'Valor produzido (milhares de reais)', 
        'Produto agrícola',
        'VALOR_PROD'
        )
with col3:
    bar_plot(
        atv_agr, 
        'REND_AREA', 
        'PRODUTO', 
        'Produtos agrícolas com maior rendimento', 
        'Valor produzido/Área plantada', 
        'Produto agrícola',
        'REND_AREA'
        )
    