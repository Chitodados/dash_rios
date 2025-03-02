import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from io import BytesIO
import requests
import os
from datetime import datetime

st.markdown("""
    # Monitoramento e Previsão dos Níveis de Água dos Rios

    **Cenário:** Sua empresa importa produtos por portos ligados a rios estratégicos. Alguns desses produtos possuem alta sazonalidade de venda no verão. No entanto, existe um histórico de redução significativa na cota dos rios devido à seca, o que pode inviabilizar o transporte por algumas rotas. Diante disso, é essencial monitorar os níveis de água dos rios e projetar tendências futuras para antecipar decisões estratégicas e mitigar riscos.

    **Processo proposto:**
    - **Coleta de dados:** Extração automática ([web scraping](https://github.com/Chitolina/dash_rios/blob/main/webscrapping_dash.py/)) de informações brutas da fonte confiável ([Proama Amazonas](https://proamanaus.com.br/nivel-dos-rios/));
    - **Manipulação e análise:** Processamento dos dados e criação de gráficos informativos utilizando Python;
    - **Projeção futura:** Aplicação de modelos de séries temporais (ARIMA) para prever os níveis futuros dos rios;
    - **Deploy dinâmico:** Dashboard interativo para visualização das análises e previsões.
""", unsafe_allow_html=True)

# Configuração do seaborn
sns.set(style='whitegrid')

# Caminho do arquivo CSV
CSV_PATH = "nivel_dos_rios.csv"

# Função para carregar os dados (com cache)
@st.cache_data
def load_data():
    if not os.path.exists(CSV_PATH):
        st.error("⚠️ O arquivo CSV com os dados não foi encontrado. Aguarde a próxima atualização ou verifique o processo de scraping.")
        return None

    df = pd.read_csv(CSV_PATH)

    # Ajuste de datas e criação de colunas auxiliares
    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
    df['Dia'] = df['Data'].dt.day
    df['Mês'] = df['Data'].dt.month
    df['Ano'] = df['Data'].dt.year.astype('Int64')

    # Transformação dos dados
    df_melted = df.melt(id_vars=['Data', 'Dia', 'Mês', 'Ano'], var_name='Rio', value_name='Cota').dropna(subset=['Cota'])
    df_melted = df_melted.rename(columns={'Rio': 'rio', 'Ano': 'year', 'Mês': 'month', 'Dia': 'day', 'Cota': 'altura'})

    # Remover rios inconsistentes
    df_melted = df_melted[~df_melted['rio'].isin(['Stº. Ant. Içá', 'Iquitos', 'Coari'])]

    # Ajustar nomes dos rios
    df_melted['rio'] = df_melted['rio'].replace({
        'Tabatinga': 'Tabatinga: Solimões',
        'Itacoatiara': 'Itacoatiara: Rio Amazonas',
        'Manaus': 'Manaus: Rio Amazonas'
    })

    return df_melted

# Carregar os dados
df = load_data()

# Função para prever o ARIMA (com cache)
@st.cache_data
def forecast_arima(rio_data, months_to_predict=12):
    model = ARIMA(rio_data, order=(1, 1, 1))
    model_fit = model.fit()
    forecast = model_fit.forecast(steps=months_to_predict)
    return forecast

# Realizando a previsão para 2025 (com cache)
@st.cache_data
def get_2025_forecast(df):
    df_2025_forecast = pd.DataFrame()
    
    # Determinar o último mês real disponível
    data_atual = datetime.now()
    mes_atual = data_atual.month

    for rio in df['rio'].unique():
        for month in range(mes_atual, 13):
            rio_month_data = df[(df['rio'] == rio) & (df['month'] == month) & (df['year'] < 2025)]
            if not rio_month_data.empty:
                forecast_values = forecast_arima(rio_month_data['altura'])
                forecast_df = pd.DataFrame({
                    'year': [2025] * len(forecast_values),
                    'month': [month] * len(forecast_values),
                    'rio': [rio] * len(forecast_values),
                    'altura': forecast_values
                })
                df_2025_forecast = pd.concat([df_2025_forecast, forecast_df], ignore_index=True)

    return df_2025_forecast

if df is not None:
    df_2025_forecast = get_2025_forecast(df)
    df_concat = pd.concat([df, df_2025_forecast])

    # Sidebar
    selected_river = st.sidebar.selectbox('Escolha a cidade/rio:', df['rio'].unique())
    anos_selecionados = st.sidebar.multiselect('Escolha os anos para comparar:', sorted(df['year'].unique()), default=[2024, 2025])

    # Filtrando os dados para o gráfico
    graficos = df_concat[(df_concat['rio'] == selected_river) & (df_concat['year'].isin(anos_selecionados))]

    # Gráfico
    st.markdown("### Evolução da cota ao longo dos meses e anos")
    if not graficos.empty:
        plt.figure(figsize=(12, 6))

        # Dados históricos (linhas contínuas)
        sns.lineplot(data=graficos[graficos['year'] < 2025], x='month', y='altura', hue='year', style='year', markers=True, dashes=False, palette='viridis')

        # Dados de 2025 existentes (linhas contínuas) e previsões (tracejadas)
        if 2025 in anos_selecionados:
            dados_2025_reais = graficos[(graficos['year'] == 2025) & (graficos['month'] <= datetime.now().month)]
            previsoes_2025 = graficos[(graficos['year'] == 2025) & (graficos['month'] > datetime.now().month)]

            sns.lineplot(data=dados_2025_reais, x='month', y='altura', color='blue', linestyle='-', label='Dados reais 2025')
            sns.lineplot(data=previsoes_2025, x='month', y='altura', color='red', linestyle='--', label='Previsão 2025')

        plt.title(f'{selected_river}', fontsize=16)
        plt.xlabel('Mês', fontsize=14)
        plt.ylabel('Cota (m)', fontsize=14)
        plt.legend(title='Ano')
        st.pyplot(plt.gcf())
    else:
        st.write("Nenhum dado disponível para o gráfico.")

    # Exibição da tabela
    st.dataframe(graficos, use_container_width=True)
else:
    st.write("Os dados ainda não foram carregados.")

st.markdown("---")
st.write("**Fonte:** [Proama Amazonas](https://proamanaus.com.br/nivel-dos-rios)")
st.write("**Desenvolvido por:** Lucas Chitolina")
