# -*- coding: utf-8 -*-
"""
Created on Tue Aug  6 11:12:59 2024

@author: 155682
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Configuração do seaborn
sns.set(style='whitegrid')

# Carregue o DataFrame
df = pd.read_excel('nivel_dos_rios_ultimos_5_anos.xlsx')

# Converta a coluna 'Data' para o formato de data
df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
df['Month'] = df['Data'].dt.month
df['Year'] = df['Data'].dt.year

# Crie a interface do usuário
st.title('Dashboard dos Níveis dos Rios')

# Selecione a data
data_min = df['Data'].min()
data_max = df['Data'].max()
selected_date = st.date_input('Escolha a data', value=data_max, min_value=data_min, max_value=data_max)

# Selecione o rio
available_rivers = df.columns[1:]  # Assume que a primeira coluna é a data
selected_river = st.selectbox('Escolha o rio', available_rivers)

# Filtra os dados com base na data e o rio selecionado
filtered_data = df[df['Data'] == pd.to_datetime(selected_date)]

if not filtered_data.empty:
    # Agrupa os dados por rio
    rios = df.groupby(selected_river)

    for rio, data in rios:
        plt.figure(figsize=(18, 8))

        # Plot das linhas com transparência padrão (1.0) e incluir na legenda
        sns.lineplot(data=data, x="Month", y="Data", hue="Year", palette="husl", linewidth=3, estimator='mean', errorbar='sd')

        # Plot das sombras dos desvios com maior transparência (alpha=0.2) e não incluir na legenda
        sns.lineplot(data=data, x="Month", y="Data", hue="Year", palette="husl", linewidth=0, estimator='mean', errorbar='sd', alpha=0.1, legend=False)

        sns.despine(offset=10, trim=True)
        plt.legend(loc='upper right')
        plt.xticks(ticks=range(1, 13))
        plt.xlabel('Mês', fontsize=14)
        plt.ylabel('Cota (m)', fontsize=14)
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)
        plt.gca().spines['left'].set_linewidth(1.5)
        plt.gca().spines['bottom'].set_linewidth(1.5)
        plt.gca().spines['left'].set_color('gray')
        plt.gca().spines['bottom'].set_color('gray')
        plt.gca().tick_params(axis='both', which='major', labelsize=12, color='gray', width=1.5)
        plt.gca().set_facecolor('#f0f0f0')

        # Mostra o gráfico no Streamlit
        st.pyplot(plt)

else:
    st.write('Nenhum dado disponível para a data e o rio selecionados.')
        st.pyplot(plt)

else:
    st.write('Nenhum dado disponível para a data e o rio selecionados.')
