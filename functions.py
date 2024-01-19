# -*- coding: utf-8 -*-
"""
Created on Wed Jan 17 12:46:31 2024

@author: D732506
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
import streamlit as st

pio.templates.default = "plotly"


# FUNCTIONS
def create_df_from_lists(cod, name, param, value, p5, p95, comments):
    
    df = pd.DataFrame(
        {'est': cod,
         'nombre': name,
         'parametro': param,
         'valor': value,
         'P5': p5,
         'P95': p95,
         'comentario': comments
         })
    
    return df


def delete_no_samples(df):
    
    df.dropna(subset=['ta_agua', 'ph_insitu', 'cond_insitu', 'o2percent_insitu', 'o2_insitu'], how='all', inplace=True)

    return


def export_df(df, out):

    df.to_excel(out)
    
    return


def file_code_processing(df):
    
    # Algunos excel del laboratorio traen la N de prefijo de codigo
    df['est'] = df['estacion'].apply(str)
    df['est'] = df['est'].str.replace('Nº ','')
    # Quitar espacios en blanco en el codigo al inicio y al final
    df['est'] = df['est'].str.strip()
    df.drop(['estacion'], axis=1, inplace=True)
    
    return


def file_processing(df):
    
    # Borrar nombre de rio y municipio de la tabla del laboratorio
    #df_clean = df.drop(['Río', 'Municipio'], axis=1)
    df_clean = df.drop(['Municipio'], axis=1)
    # Coger solo la fecha de la columna_timestamp que viene con todos los datos fecha y hora
    df_clean['fecha'] = df_clean['time_stamp'].dt.date
    # Borrar time_stamp
    df_clean2 = df_clean.drop(['time_stamp'], axis=1)
    # Borrar la columna Unnamed si existe
    df_clean2 = df_clean2.loc[:, ~df_clean2.columns.str.startswith('Unnamed')]
    # Borrar Duplicados y Blancos del resultado del laboratorio
    df_processed = df_clean2[~df_clean2.n_analisis.str.contains("DB")]
    file_code_processing(df_processed)
    
    # Quitar el no detectado y convertir en 0
    df_processed.loc[df_processed['e_coli'] == 'No detectado', 'e_coli'] = '0'
    df_processed.loc[df_processed['coliformes_totales'] == 'No detectado', 'coliformes_totales'] = '0'
    
    return df_processed


def get_dates(df):

    min_date = df['fecha'].min().strftime('%Y-%m-%d')
    max_date = df['fecha'].max().strftime('%Y-%m-%d')    
    
    return (min_date, max_date)


def historic_review(historic_data, analysis_data, cod_stations, param_columns):
        
    LIST_PARAM = []
    LIST_EST = []
    LIST_NAME = []
    LIST_P5 = []
    LIST_P95 = []
    LIST_VALUE = []
    LIST_COMM = []

    for cod in cod_stations:    
        
        df_estacion_historic = historic_data.loc[[cod]]
        df_stats_historic = df_estacion_historic.describe(percentiles=[.05, .95]).loc()[['5%','95%']]
        df_stats_historic.rename(index={'5%': 'P5', '95%': 'P95'}, inplace=True)    
    
        for param in param_columns:        
        
            param_value = analysis_data.loc[[cod]].iloc[0][param]
            historic_P5 = df_stats_historic.loc[['P5']].iloc[0][param]
            historic_P95 = df_stats_historic.loc[['P95']].iloc[0][param]
        
            if param == 'e_coli' or param == 'coliformes_totales':
                
                pass
            
            elif param == 'mat_org' or param == 'nh4' or param == 'no2' or param == 'po4' or param == 'solidos_susp':
                
                if param_value > historic_P95:
                    
                    LIST_PARAM.append(param)
                    LIST_EST.append(analysis_data.loc[[cod]].index[0])
                    LIST_NAME.append(analysis_data.loc[[cod]].iloc[0]['nombre'])
                    LIST_P5.append(historic_P5)
                    LIST_P95.append(historic_P95)
                    LIST_VALUE.append(param_value)
                    LIST_COMM.append('Valor > P95')
            
            else:
                
                if param_value < historic_P5 or param_value > historic_P95:            

                    LIST_PARAM.append(param)
                    LIST_EST.append(analysis_data.loc[[cod]].index[0])
                    LIST_NAME.append(analysis_data.loc[[cod]].iloc[0]['nombre'])
                    LIST_P5.append(historic_P5)
                    LIST_P95.append(historic_P95)
                    LIST_VALUE.append(param_value)
                    if param_value < historic_P5:
                        LIST_COMM.append('Valor < P5')
                    else:
                        LIST_COMM.append('Valor > P95')
                        
    df = create_df_from_lists(LIST_EST, LIST_NAME, LIST_PARAM, LIST_VALUE, LIST_P5, LIST_P95, LIST_COMM)
    df.sort_values(by='est', inplace=True)
    #df.to_excel('historico2.xlsx')
    st.dataframe(df)
    
    return


def join_dfs(df1, df2, field, mode):

    merged = df1.merge(df2, on=field, how=mode)
    #df1 = df1.merge(df2[["Key_Column", "Target_Column1", "Target_Column2"]])
    
    return merged


def metales_pesados_calc(df):

    df['as_'] = df['as_'] / 1000
    df['cd'] = df['cd'] / 1000
    df['cr'] = df['cr'] / 1000
    df['cu'] = df['cu'] / 1000
    df['fe'] = df['fe'] / 1000
    df['hg'] = df['hg'] / 1000
    df['mn'] = df['mn'] / 1000
    df['ni'] = df['ni'] / 1000
    df['pb'] = df['pb'] / 1000
    df['se'] = df['se'] / 1000
    df['zn'] = df['zn'] / 1000
    
    return 


def plot_data(df, type_viz):
    
    plot_regression(df, 'cond_lab', 'cond_insitu', 'CONDUCTIVIDAD LABORATORIO VS CONDUCTIVAD CAMPO', 'valid_cond')
    plot_regression(df, 'ph_lab', 'ph_insitu', 'PH LABORATORIO VS PH CAMPO', 'valid_ph')
    plot_regression(df, 'e_coli', 'coliformes_totales', 'E.COLI VS COLIFORMES TOTALES', 'valid_ecoli')
    plot_regression(df, 'po4', 'ptot', 'FOSFATOS VS FOSFORO TOTAL', 'valid_po4')
    
    if type_viz== 'COMPLETO':
        
        plot_regression(df, 'dureza', 'dureza_calc', 'DUREZA LABORATORIO VS DUREZA CALCULADA', 'valid_dureza')
        plot_regression(df, 'co3h', 'tic', 'BICARBONATOS VS TIC', 'valid_co3h')
        plot_regression(df, 'cationes', 'aniones', 'CATIONES VS ANIONES', 'valid_ebc')
    
    
    return


def plot_regression(df, x, y, title, color=''):
    
    '''color_dict= {'True': 'red',
                 'False': 'lightgreen'
                 }'''
    
    fig = px.scatter(df, x=x, y=y, title=title, color= color, hover_name='est', hover_data=['nombre'])
    #fig.show()
    st.plotly_chart(fig, use_container_width=True, theme=None)
    
    return


def rename_cols_field_data(df):
    
    renamed = df.rename(columns = {
        df.columns[0]: 'est',
        df.columns[3]: 'ph_insitu',
        df.columns[4]: 'cond_insitu',
        df.columns[5]: 'o2percent_insitu',
        df.columns[6]: 'o2_insitu'
        })
    
    return renamed



def rename_cols_original_file(df):
    
    if len(df.columns) > 21:
        
        renamed = df.rename(columns = {
            df.columns[0]: 'n_analisis', 
            df.columns[1]: 'estacion',
            df.columns[2]: 'rio',
            df.columns[4]: 'time_stamp',
            df.columns[5]: 'ph_lab', 
            df.columns[6]: 'cond_lab',
            df.columns[7]: 'mat_org', 
            df.columns[8]: 'cl',
            df.columns[9]: 'so4', 
            df.columns[10]: 'no3',
            df.columns[11]: 'no2',
            df.columns[12]: 'nh4', 
            df.columns[13]: 'ptot',
            df.columns[14]: 'po4', 
            df.columns[15]: 'solidos_susp',
            df.columns[16]: 'tic',
            df.columns[17]: 'toc',
            df.columns[18]: 'dbo5',
            df.columns[19]: 'e_coli',
            df.columns[20]: 'coliformes_totales',
            df.columns[21]: 'dureza',
            df.columns[22]: 'ca',
            df.columns[23]: 'mg',
            df.columns[24]: 'co3',
            df.columns[25]: 'co3h',
            df.columns[26]: 'na',
            df.columns[27]: 'k',
            df.columns[28]: 'as_',
            df.columns[29]: 'cd',
            df.columns[30]: 'cr',
            df.columns[31]: 'cu',
            df.columns[32]: 'fe',
            df.columns[33]: 'hg',
            df.columns[34]: 'mn',
            df.columns[35]: 'ni',
            df.columns[36]: 'pb',
            df.columns[37]: 'se',
            df.columns[38]: 'zn'
            })
    else:
        
        renamed = df.rename(columns = {
            df.columns[0]: 'n_analisis', 
            df.columns[1]: 'estacion',
            df.columns[2]: 'rio',
            df.columns[4]: 'time_stamp',
            df.columns[5]: 'ph_lab', 
            df.columns[6]: 'cond_lab',
            df.columns[7]: 'mat_org', 
            df.columns[8]: 'cl',
            df.columns[9]: 'so4', 
            df.columns[10]: 'no3',
            df.columns[11]: 'no2',
            df.columns[12]: 'nh4', 
            df.columns[13]: 'ptot',
            df.columns[14]: 'po4', 
            df.columns[15]: 'solidos_susp',
            df.columns[16]: 'tic',
            df.columns[17]: 'toc',
            df.columns[18]: 'dbo5',
            df.columns[19]: 'e_coli',
            df.columns[20]: 'coliformes_totales'
        })
        
        renamed['dureza'] = np.NaN
        renamed['ca'] = np.NaN
        renamed['mg'] = np.NaN
        renamed['co3'] = np.NaN
        renamed['co3h'] = np.NaN
        renamed['na'] = np.NaN
        renamed['k'] = np.NaN
        renamed['as_'] = np.NaN
        renamed['cd'] = np.NaN
        renamed['cr'] = np.NaN
        renamed['cu'] = np.NaN
        renamed['fe'] = np.NaN
        renamed['hg'] = np.NaN
        renamed['mn'] = np.NaN
        renamed['ni'] = np.NaN
        renamed['pb'] = np.NaN
        renamed['se'] = np.NaN
        renamed['zn'] = np.NaN

    return renamed


def replace_comma(df, col_names):
    
    df[col_names] = df[col_names].applymap(lambda x: str(x))
    df[col_names] = df[col_names].applymap(lambda x: x.replace(',','.'))

    return
    

def symbols_calculation(df, col_names):
    
    df[col_names] = df[col_names].applymap(lambda x: (x[1:]) if x.startswith('>') else x)    
    df[col_names] = df[col_names].applymap(lambda x: float(x[1:])/2 if x.startswith('<') else float(x))
    
    numeric_df = df.replace("nan", np.NaN, regex=True)

    return numeric_df
    

def valid_analysis(df, type_analysis):
    
    # CONDUCTIVIDAD LABORATORIO VS CONDUCTIVIDAD CAMPO
    df['ratio_cond'] = abs(((df['cond_lab'] - df['cond_insitu'])/ df['cond_lab'])*100)   
    df['valid_cond'] = df['ratio_cond'] > 10
    #print(df.loc[df['valid_cond']==True])

    # PH LABORATORIO VS PH CAMPO
    df['ratio_ph'] = abs(((df['ph_lab'] - df['ph_insitu'])/ df['ph_lab'])*100)
    df['valid_ph'] = df['ratio_ph'] > 10
    #print(df.loc[df['valid_ph']==True])

    # RATIO ECOLI / COLIFORMES TOTALES
    df['ratio_ecoli'] = df['e_coli'] / df['coliformes_totales']
    df['valid_ecoli'] = df['ratio_ecoli'] > 1
    #print(df.loc[df['valid_ecoli']==True])

    # RATIO FOSFATOS / FOSFORO TOTAL
    df['ratio_po4'] = (df['po4'] * (31/95)) / df['ptot']
    df['valid_po4'] = df['ratio_po4'] > 1
    #print(df.loc[df['valid_po4']==True])
    
    if type_analysis == 'COMPLETO':
        
        # DUREZA LABORATORIO VS DUREZA CALCULADA
        df['dureza_calc'] = ((2.5 * df['ca']) + (4.116 * df['mg'])) / 10
        df['ratio_dureza'] = abs((df['dureza_calc'] - df['dureza']) / df['dureza_calc'])
        df['valid_dureza'] = df['ratio_dureza'] > 1
        #print(df.loc[df['valid_dureza']==True])

        # TIC VS BICARBONATOS
        df['valid_co3h'] = (df['co3h'] / 61) > df['tic']
        #print(df.loc[df['valid_co3h']==True])

        # BALANCE IONICO
        df['cationes'] = (df['na']/22.99) + (df['k']/39.098) + (df['ca']/(40.078/2)) + (df['mg']/(24.305/2))
        df['aniones'] = (df['cl']/35.45) + (df['so4']/(96.056/2)) + (df['co3h']/61.016) + (df['no3']/62.004)
        df['ebc'] = abs(200*((df['cationes'] - df['aniones'])/(df['cationes'] + df['aniones'])))
        df['valid_ebc'] = df['ebc'] > 15
        #print(df.loc[df['valid_ebc']==True])

    
    return