import functions as f
import pandas as pd
import streamlit as st
import plotly.io as pio
import warnings


st.set_page_config(page_title='ANALITICAS RIOS')
pio.templates.default = 'plotly_white'
pd.options.mode.chained_assignment = None
warnings.simplefilter(action='ignore', category=UserWarning)


st.header(':droplet: Revisión muestreos aguas superficiales')

st.write(':microscope: RESULTADOS LABORATORIO:')

# SUBIR EL ARCHIVO DE LABORATORIO      
LAB_FILE = st.file_uploader('Elige un archivo')

if LAB_FILE is not None:    
    
    ANALYSIS_OP = ['BASICO','COMPLETO'] # BASICO O COMPLETO

    # --- STREAMLIT SELECTION
    ANALYSIS_TYPE = st.selectbox(label=':mag_right: TIPO DE ANÁLISIS', options=ANALYSIS_OP, index=None, placeholder='Elige una opción...')
    
        
    if st.button('VERIFICAR'):       
             
        
        PROCESSING_COLS = ['ph_lab','cond_lab','mat_org','cl','so4','no3','no2','nh4','ptot','po4','solidos_susp',
                   'tic','toc','dbo5','e_coli','coliformes_totales','dureza','ca','mg','co3','co3h','na',
                   'k','as_','cd','cr','cu','fe','hg','mn','ni','pb','se','zn']        

        #############################################################################################################################
        # DATA INPUT
        #############################################################################################################################
        
        # LAB DATA
        data = pd.read_excel(LAB_FILE, converters={'Código':str})
        # STATIONS
        data_est = pd.read_csv('estaciones_rios.csv', low_memory=False)
        data_est = data_est[['est','nombre']]
        # HISTORIC DATA
        data_hist = pd.read_csv('historic_rios.csv', low_memory=False)
        data_hist = data_hist[['est','ph_lab','cond_lab','mat_org','cl','so4','no3','no2','nh4','ptot','po4','solidos_susp','tic','toc','dbo5','e_coli','coliformes_totales','dureza','ca','mg','co3','co3h','na','k','as_','cd','cr','cu','fe','hg','mn','ni','pb','se','zn']]
        # FIELD DATA
        data_field = pd.read_csv('rios_campo.csv', low_memory=False)
        data_field = data_field[['cod_estacion','fecha','ta_agua','ph','conductividad','od_percent','od_ppm']]    
        data_field['fecha'] = pd.to_datetime(data_field['fecha'])
        
        #############################################################################################################################
        # PROCESSING
        #############################################################################################################################
        
        # LAB FILE PROCESSING
        data_r = f.rename_cols_original_file(data)
        df_analysis = f.file_processing(data_r)
        f.replace_comma(df_analysis, PROCESSING_COLS)
        df_lab = f.symbols_calculation(df_analysis, PROCESSING_COLS)
        f.metales_pesados_calc(df_lab)
        # GET DATES FROM LAB FILE
        MIN_DAY, MAX_DAY = f.get_dates(df_lab)        
        MIN_DAY = pd.to_datetime(MIN_DAY)
        MAX_DAY = pd.to_datetime(MAX_DAY)
        # GET FIELD DATA FOR THE SELECTED DATES        
        valid_df = data_field[data_field['fecha'].between(MIN_DAY, MAX_DAY)]
        # FIELD DATA PROCESSING
        df_field = f.rename_cols_field_data(valid_df)
        f.delete_no_samples(df_field)
        # JOIN LAB-FIELD-STATION DATA
        df_data = f.join_dfs(df_field, df_lab, 'est', 'inner')
        df_all = f.join_dfs(df_data, data_est, 'est', 'inner')
        # GET THE CODES FOR THE ANALYZED POINTS
        CODE_LIST = df_all['est'].unique().tolist()        

        #############################################################################################################################
        # VALIDATIONS & VISUALIZATIONS
        #############################################################################################################################
        
        with st.spinner('Calculando validaciones y generando gráficas...'):
             
             f.valid_analysis(df_all, ANALYSIS_TYPE)
        
        
        #############################################################################################################################
        # HISTORIC COMPARISON
        #############################################################################################################################
        
        df_c = df_all[['est','nombre','ph_lab','cond_lab','mat_org','cl','so4','no3','no2','nh4','ptot',
               'po4','solidos_susp','tic','toc','dbo5','e_coli','coliformes_totales','dureza','ca',
               'mg','co3','co3h','na','k','as_','cd','cr','cu','fe','hg','mn','ni','pb','se','zn']]

        df_c.set_index('est', inplace=True)
        data_hist.set_index('est', inplace=True)        
               
        st.write(':spiral_calendar_pad: COMPARACIÓN CON LA SERIE HISTÓRICA (Percentil 5 y Percentil 95):')
        
        with st.spinner('Comparando con el histórico...'):
            
            f.historic_review(data_hist, df_c, CODE_LIST, PROCESSING_COLS)    
