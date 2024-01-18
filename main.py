# -*- coding: utf-8 -*-
"""
Created on Wed Jan 17 12:47:14 2024

@author: D732506
"""

import functions as f
import pandas as pd
import streamlit as st
import plotly.io as pio
import warnings

pio.templates.default = "plotly_white"
pd.options.mode.chained_assignment = None
warnings.simplefilter(action='ignore', category=UserWarning) 


st.set_page_config(page_title='ANALITICAS RIOS')
st.header(':droplet: Revisión muestreos aguas superficiales')

st.write(':microscope: RESULTADOS LABORATORIO:')
        
LAB_FILE = st.file_uploader('Elige un archivo')

if LAB_FILE is not None:    
    
    ANALYSIS_OP = ['BASICO','COMPLETO'] # BASICO O COMPLETO

    # --- STREAMLIT SELECTION
    ANALYSIS_TYPE = st.selectbox(label=':mag_right: TIPO DE ANÁLISIS', options=ANALYSIS_OP, index=None, placeholder='Elige una opción...')
    
        
    if st.button('VERIFICAR'):        
        
        DB_CONN_STRING = 'postgresql://editor:editor123@10.242.134.47:5432/hidrologia'
        DB_CONNECTION = f.database_conn(DB_CONN_STRING)       
        
        PROCESSING_COLS = ['ph_lab','cond_lab','mat_org','cl','so4','no3','no2','nh4','ptot','po4','solidos_susp',
                   'tic','toc','dbo5','e_coli','coliformes_totales','dureza','ca','mg','co3','co3h','na',
                   'k','as_','cd','cr','cu','fe','hg','mn','ni','pb','se','zn']        

        QUERY_EST = """SELECT est, nombre FROM red_calidad.estaciones_rios"""
        QUERY_HISTORIC ="""SELECT est, ph_lab, cond_lab, mat_org, cl, so4, no3, no2, nh4, ptot, po4, solidos_susp, tic, toc, dbo5, e_coli, coliformes_totales, dureza, ca, mg, co3, co3h, na, k, as_, cd, cr, cu, fe, hg, mn, ni, pb, se, zn FROM red_calidad.historic_rios"""
        data_est = f.query_db_tables(QUERY_EST, DB_CONNECTION)
        data_hist = f.query_db_tables(QUERY_HISTORIC, DB_CONNECTION)

        data = pd.read_excel(LAB_FILE, converters={'Código':str})
        data_r = f.rename_cols_original_file(data)
        df_analysis = f.file_processing(data_r)
        f.replace_comma(df_analysis, PROCESSING_COLS)
        df_lab = f.symbols_calculation(df_analysis, PROCESSING_COLS)
        f.metales_pesados_calc(df_lab)
        MIN_DAY, MAX_DAY = f.get_dates(df_lab)
        QUERY_FIELD = f.query_field_data(MIN_DAY, MAX_DAY)

        data_field = f.query_db_tables(QUERY_FIELD, DB_CONNECTION)
        df_field = f.rename_cols_field_data(data_field)
        f.delete_no_samples(df_field)
        df_data = f.join_dfs(df_field, df_lab, 'est', 'inner')
        df_all = f.join_dfs(df_data, data_est, 'est', 'inner')
        CODE_LIST = df_all['est'].unique().tolist()

        # VALIDATIONS
        f.valid_analysis(df_all, ANALYSIS_TYPE)

        # VIZ
        f.plot_data(df_all, ANALYSIS_TYPE)

        df_c = df_all[['est','nombre','ph_lab','cond_lab','mat_org','cl','so4','no3','no2','nh4','ptot',
               'po4','solidos_susp','tic','toc','dbo5','e_coli','coliformes_totales','dureza','ca',
               'mg','co3','co3h','na','k','as_','cd','cr','cu','fe','hg','mn','ni','pb','se','zn']]

        df_c.set_index('est', inplace=True)
        data_hist.set_index('est', inplace=True)        
               
        st.write(':spiral_calendar_pad: COMPARACIÓN CON LA SERIE HISTÓRICA (Percentil 5 y Percentil 95):')
        
        with st.spinner('Calculando...'):
            
            f.historic_review(data_hist, df_c, CODE_LIST, PROCESSING_COLS)
                
    