import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.linear_model import LinearRegression
from io import BytesIO
import requests

# Configuração do seaborn
sns.set(style='whitegrid')

# URL do arquivo Excel no GitHub
file_url = "https://raw.githubusercontent.com/Chitolina/dash_rios/main/dados_rios/nivel_dos_rios_ultimos_5_anos.xlsx"

# Baixar o conteúdo do arquivo usando requests
response = requests.get(file_url)

# Verificar se o download foi bem-sucedido
if response.status_code == 200:
    file_content = BytesIO(response.content)
    df = pd.read_excel(file_content)
else:
    st.error("Erro ao baixar o arquivo do GitHub")
    st.stop()

# Fragmentar a coluna 'Data' em colunas separadas de dia, mês e ano
df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
df['Dia'] = df['Data'].dt.day
df['Mês'] = df['Data'].dt.month
df['Ano'] = df['Data'].dt.year.astype(int)

# Transformar o DataFrame em formato longo
df_melted = df.melt(id_vars=['Data', 'Dia', 'Mês', 'Ano'], var_name='Rio', value_name='Cota')
df_melted = df_melted.dropna(subset=['Cota'])

# Ajustar nomes dos rios
dic = {
    'Tabatinga': 'Tabatinga: Solimões',
    'Itacoatiara': 'Itacoatiara: Rio Amazonas',
    'Manaus': 'Manaus: Rio Amazonas'
}
df_melted['Rio'] = df_melted['Rio'].replace(dic)

df = df_melted[['Ano', 'Mês', 'Dia', 'Rio', 'Cota']].rename(columns={
    'Rio': 'rio', 'Ano': 'year', 'Mês': 'month', 'Dia': 'day', 'Cota': 'altura'
})
df = df.fillna(0)

# Filtrar rios indesejados
df = df.loc[~df['rio'].isin(['Stº. Ant. Içá', 'Iquitos', 'Coari'])]

# Configurar opções no dashboard
rios = df['rio'].unique()
selected_river = st.sidebar.selectbox('Escolha a cidade/rio:', rios)

meses = list(range(1, 13))
meses_selecionados = st.sidebar.multiselect('Escolha os meses (para a tabela):', options=["Todos os meses"] + meses, default=["Todos os meses"])

anos = sorted(df['year'].unique())
anos_selecionados = st.sidebar.multiselect('Escolha os anos para comparar:', options=["Todos os anos"] + anos, default=["Todos os anos"])

# Aplicar filtros para "Todos os meses" e "Todos os anos"
if "Todos os meses" in meses_selecionados:
    meses_selecionados = meses
if "Todos os anos" in anos_selecionados:
    anos_selecionados = anos

if len(anos_selecionados) < 2:
    st.warning('Por favor, selecione pelo menos dois anos para realizar a comparação.')
    st.stop()

# Substituir ARIMA por regressão linear
def forecast_linear_regression(rio_data, months_to_predict=12):
    X = np.array(range(1, len(rio_data) + 1)).reshape(-1, 1)
    y = rio_data.values

    model = LinearRegression()
    model.fit(X, y)

    X_future = np.array(range(len(rio_data) + 1, len(rio_data) + 1 + months_to_predict)).reshape(-1, 1)
    forecast = model.predict(X_future)
    return forecast

# Previsão para o ano de 2025
df_2025_forecast = pd.DataFrame()

for rio in df['rio'].unique():
    for month in range(1, 13):
        rio_month_data = df[(df['rio'] == rio) & (df['month'] == month) & (df['year'] < 2025)]
        if not rio_month_data.empty:
            forecast_values = forecast_linear_regression(rio_month_data['altura'])
            forecast_df = pd.DataFrame({
                'year': [2025] * len(forecast_values),
                'month': [month] * len(forecast_values),
                'rio': [rio] * len(forecast_values),
                'Previsão': forecast_values
            })
            df_2025_forecast = pd.concat([df_2025_forecast, forecast_df], ignore_index=True)

df_concat = pd.concat([df, df_2025_forecast])
graficos = df_concat[(df_concat['rio'] == selected_river) & (df_concat['year'].isin(anos_selecionados))]

# Filtrar dados para a tabela
filtrada = df[
    (df['rio'] == selected_river) & 
    (df['year'].isin(anos_selecionados)) & 
    (df['month'].isin(meses_selecionados))
]

# Estilização do dashboard
st.markdown("""
<style>
/* Personalização */
main {
    background-color: #F0F2F6;
}
</style>
""", unsafe_allow_html=True)

# Gráfico da evolução das cotas
st.markdown("### Evolução da cota ao longo dos meses e anos")
if not graficos.empty:
    plt.figure(figsize=(12, 6))
    sns.lineplot(data=graficos[graficos['year'] != 2025], x='month', y='altura', hue='year', style='year', markers=True, dashes=False, palette='viridis')
    sns.lineplot(data=graficos[graficos['year'] == 2025], x='month', y='Previsão', color='red', linestyle='--', label='Previsão 2025')
    plt.title(f'{selected_river}', fontsize=16)
    plt.xlabel('Mês', fontsize=14)
    plt.ylabel('Cota (m)', fontsize=14)
    plt.legend(title='Ano')
    st.pyplot(plt.gcf())
else:
    st.write('Nenhum dado disponível para o gráfico.')

# Tabela de variação mês a mês
st.markdown("### Tabela de Variação de Cota Média")
if not filtrada.empty:
    comparacao = []
    anos_selecionados_sorted = sorted(anos_selecionados)
    for month in sorted(filtrada['month'].unique()):
        for i in range(1, len(anos_selecionados_sorted)):
            ano_1 = anos_selecionados_sorted[i - 1]
            ano_2 = anos_selecionados_sorted[i]

            dados_ano_1 = filtrada[(filtrada['year'] == ano_1) & (filtrada['month'] == month)]['altura'].mean()
            dados_ano_2 = filtrada[(filtrada['year'] == ano_2) & (filtrada['month'] == month)]['altura'].mean()

            if pd.notna(dados_ano_1) and pd.notna(dados_ano_2):
                variation_absolute = dados_ano_2 - dados_ano_1
                variation_percentage = (variation_absolute / dados_ano_1) * 100 if dados_ano_1 != 0 else 0

                comparacao.append({
                    'Mês': month,
                    'Ano Anterior': str(ano_1),
                    'Ano Posterior': str(ano_2),
                    'Cota Média (m) Ano Anterior': f"{dados_ano_1:.1f}",
                    'Cota Média (m) Ano Posterior': f"{dados_ano_2:.1f}",
                    'Variação Absoluta (m)': f"{variation_absolute:.1f}",
                    'Variação Percentual (%)': f"{variation_percentage:.1f}%"
                })

    tabela_variacao = pd.DataFrame(comparacao)
    st.table(tabela_variacao)
else:
    st.write('Nenhuma variação encontrada.')



st.download_button(
    label="Baixar dados de variação",
    data=comparison_df.to_csv(index=False).encode('utf-8'),
    file_name=f"variacao_cota_{selected_river}.csv",
    mime="text/csv"
)

st.markdown("---")

st.write("**Fonte dos Dados:** https://proamanaus.com.br/nivel-dos-rios")
st.write("**Desenvolvido por:** [Lucas Chitolina](https://github.com/Chitolina) & [ChatGPT](https://openai.com/index/chatgpt/)")
