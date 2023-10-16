import pandas as pd
import geopandas as gpd

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

def carregar_agro():
    agro = pd.read_csv(r"C:/Users/User/Documents/GitHub/BCG2023/Dados/Tabela_final/dados_producao_agricola.csv").drop(columns='Unnamed: 0')
    return agro

def carregar_solos(_all_muns):
    solos = pd.read_csv(r"C:/Users/User/Documents/GitHub/BCG2023/Dados/Views/solos_municipios.csv").drop(columns='Unnamed: 0')
    solos = _all_muns[['IBGE7', 'NOME']].merge(solos, on = 'IBGE7', how = 'inner').drop(columns='IBGE7')
    solos['AREA_TOTAL'] = round(solos['AREA_TOTAL'],2)
    return solos

def carregar_dados_mapa():
    dados_mapa = pd.read_csv(r"C:/Users/User/Documents/GitHub/BCG2023/Dados/Views/dados_mapa.csv")
    lim_muns = pd.read_json(r'C:/Users/User/Documents/GitHub/BCG2023/Dados/Views/municipios-poligonos.json')
    lim_muns['poligono'] = [str(polygon) for polygon in lim_muns['poligono']]
    lim_muns['geometry'] = lim_muns['poligono'].apply(lambda x: shape(eval(x)))
    lim_muns = lim_muns[['municipioCodigo', 'geometry']].rename(columns={'municipioCodigo':'IBGE7'})
    dados_mapa = dados_mapa.merge(lim_muns, on = 'IBGE7', how = 'inner')
    dados_mapa = gpd.GeoDataFrame(dados_mapa, geometry='geometry')
    dados_mapa = dados_mapa.set_crs("EPSG:4326")
    return dados_mapa

def carregar_dados_knn():
    dados_knn = pd.read_csv(r"C:/Users/User/Documents/GitHub/BCG2023/Dados/Views/dataset_knn_processado.csv")
    return dados_knn



